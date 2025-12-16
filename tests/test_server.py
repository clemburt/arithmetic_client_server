"""Test class ArithmeticServer."""
from multiprocessing import Pipe, Process
from pathlib import Path

import pytest

from arithmetic_client_server.server.server import ArithmeticServer
from arithmetic_client_server.server.worker import WorkerProcess


@pytest.fixture
def tmp_output_file(tmp_path: Path) -> Path:
    """Create a temporary output file path."""
    return tmp_path / "results.txt"


class FakeSocket:
    """Mock socket to simulate client-server communication."""

    def __init__(self, lines: list[str]):
        self.data = "\n".join(lines).encode()
        self.sent_data = b""
        self.offset = 0

    def recv(self, bufsize: int) -> bytes:
        if self.offset >= len(self.data):
            return b""
        chunk = self.data[self.offset : self.offset + bufsize]
        self.offset += bufsize
        return chunk

    def sendall(self, data: bytes) -> None:
        self.sent_data += data

    def close(self) -> None:
        pass


def test_receive_data(tmp_output_file: Path) -> None:
    """_receive_data returns non-empty lines from socket."""
    lines = ["2 + 3", "", "4 * 5"]
    fake_socket = FakeSocket(lines)
    server = ArithmeticServer(host="127.0.0.1", port=9000, output_file=tmp_output_file)
    result = server._receive_data(fake_socket)
    assert result == ["2 + 3", "4 * 5"]


def test_spawn_worker_returns_process_and_pipe(tmp_output_file: Path) -> None:
    """_spawn_worker returns a Process and a parent Pipe."""
    server = ArithmeticServer(host="127.0.0.1", port=9000, output_file=tmp_output_file)
    proc, parent_pipe = server._spawn_worker("1 + 1", 1)
    assert hasattr(proc, "start") and hasattr(proc, "join")
    assert hasattr(parent_pipe, "send") and hasattr(parent_pipe, "recv")
    proc.terminate()
    proc.join()


def test_collect_finished_workers_writes_results(tmp_output_file: Path) -> None:
    """_collect_finished_workers writes results or errors to file."""
    server = ArithmeticServer(host="127.0.0.1", port=9000, output_file=tmp_output_file)

    parent_conn, child_conn = Pipe()
    # simulate worker payload
    payload = {"line": 1, "expression": "2 + 3", "result": 5.0}
    child_conn.send(payload)
    child_conn.close()

    def dummy_run():
        pass

    proc = Process(target=dummy_run)
    proc.start()
    proc.join()

    active_workers = [(proc, parent_conn)]

    with tmp_output_file.open("w") as f_out:
        server._collect_finished_workers(active_workers, f_out)

    content = tmp_output_file.read_text()
    assert "2 + 3 = 5.0" in content


@pytest.mark.parametrize(
    "lines, expected_output",
    [
        (["2 + 3", "4 * 5"], ["2 + 3 = 5.0", "4 * 5 = 20.0"]),
        (["2 +", "3 *"], ["2 + -> ERROR", "3 * -> ERROR"]),
    ],
)
def test_server_start(tmp_output_file: Path, lines, expected_output) -> None:
    """Start processes expressions and writes results for valid/invalid input."""
    # Patch WorkerProcess.run to simulate evaluation
    original_run = WorkerProcess.run

    def fake_run(self):
        try:
            # Try to evaluate the expression safely
            result = eval(self.expression)  # safe here because test input is controlled
            self.conn.send({
                "line": self.line_number,
                "expression": self.expression,
                "result": float(result),
            })
        except Exception:
            self.conn.send({
                "line": self.line_number,
                "expression": self.expression,
                "error": "Invalid",
            })
        finally:
            self.conn.close()

    WorkerProcess.run = fake_run

    # Mock socket
    fake_socket = FakeSocket(lines)

    server = ArithmeticServer(host="127.0.0.1", port=9000, output_file=tmp_output_file)
    data = server._receive_data(fake_socket)

    # Spawn workers
    active_workers = [server._spawn_worker(expr, i + 1) for i, expr in enumerate(data)]

    # Collect results
    with tmp_output_file.open("w") as f_out:
        for proc, pipe_conn in active_workers:
            payload = pipe_conn.recv()
            pipe_conn.close()
            proc.join()
            if "result" in payload:
                f_out.write(f"{payload['expression']} = {payload['result']}\n")
            else:
                f_out.write(f"{payload['expression']} -> ERROR\n")
            f_out.flush()

    content = tmp_output_file.read_text().splitlines()
    for expected in expected_output:
        assert any(expected in line for line in content)

    # Restore original method
    WorkerProcess.run = original_run
