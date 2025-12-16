"""TCP server that evaluates arithmetic expressions using worker processes."""
from multiprocessing import Pipe, Process, cpu_count
from pathlib import Path
import socket
from typing import List, Tuple

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from arithmetic_client_server.common.logger import logger
from arithmetic_client_server.server.worker import WorkerProcess


class ArithmeticServer(BaseModel):
    """
    TCP socket server handling arithmetic expressions from clients.

    Features:
        - Spawns one worker process per expression.
        - Writes results immediately to disk as soon as a worker finishes.
        - Ensures each worker is destroyed immediately after finishing.
        - Handles multiple simultaneous workers up to CPU core count.
    """

    # Allow arbitrary types like multiprocessing.Connection
    model_config = ConfigDict(arbitrary_types_allowed=True)

    host: IPvAnyAddress = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=9000, ge=1, le=65535, description="Server TCP port")
    output_file: Path = Field(..., description="Path to write computation results")

    def _receive_data(self, conn: socket.socket) -> List[str]:
        """
        Receive all data from the client connection and return non-empty lines.

        :param socket.socket conn: Connected client socket

        :return: List of non-empty expression lines
        :rtype: List[str]
        """
        # Note: chunks are small pieces of data read from a TCP stream, as data may arrive in multiple packets
        chunks: List[bytes] = []
        while True:
            chunk: bytes = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        data: List[str] = b"".join(chunks).decode().splitlines()
        # Remove empty lines
        return [line.strip() for line in data if line.strip()]

    def _spawn_worker(self, expr: str, line_number: int) -> Tuple[Process, Pipe]:
        """
        Spawn a WorkerProcess for the given expression and return process and pipe.

        :param str expr: Arithmetic expression
        :param int line_number: Line number of expression in input

        :return: Tuple of (Process, parent_pipe)
        :rtype: Tuple[Process, Pipe]
        """
        parent_conn, child_conn = Pipe()
        worker = WorkerProcess(conn=child_conn, expression=expr, line_number=line_number)
        process = Process(target=worker.run)
        process.start()
        return process, parent_conn

    def _collect_finished_workers(
        self, active_workers: List[Tuple[Process, Pipe]], f_out
    ) -> None:
        """
        Collect results from all finished workers and write them to the output file.

        Finished workers are removed from the active_workers list.

        :param list active_workers: List of tuples (Process, Pipe)
        :param file f_out: Open file handle for writing results
        """
        # Iterate in reverse to safely remove finished workers while iterating
        for i in reversed(range(len(active_workers))):
            proc, pipe_conn = active_workers[i]
            if not proc.is_alive():
                # Receive payload from worker
                payload = pipe_conn.recv()
                pipe_conn.close()
                proc.join()
                active_workers.pop(i)

                # Write output immediately
                if "result" in payload:
                    f_out.write(f"{payload['expression']} = {payload['result']}\n")
                else:
                    f_out.write(f"{payload['expression']} -> ERROR: {payload['error']}\n")
                f_out.flush()

    def start(self) -> None:
        """
        Start the TCP server, accept client connections, and process arithmetic expressions.

        Steps:
            1. Bind and listen on the specified host and port.
            2. Accept a single client connection.
            3. Receive all expressions from the client.
            4. Spawn worker processes for each expression, respecting max CPU cores.
            5. Write results to output file immediately after worker finishes.
            6. Send the final results back to the client.

        :return: None
        """
        logger.info(f"🖥️ Starting server on {self.host}:{self.port}")

        # Create TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            logger.info("🖥️ Server listening")

            # Accept a single client connection
            conn, _ = s.accept()
            with conn, self.output_file.open("w", encoding="utf-8") as f_out:

                # Receive all expressions from client
                data: List[str] = self._receive_data(conn)

                # Limit number of active workers to CPU cores or number of expressions
                max_workers: int = min(cpu_count(), len(data))
                active_workers: List[Tuple[Process, Pipe]] = []

                for line_number, expr in enumerate(data, start=1):
                    # Wait until a worker slot is available
                    while len(active_workers) >= max_workers:
                        self._collect_finished_workers(active_workers, f_out)

                    # Spawn new worker for current expression
                    active_workers.append(self._spawn_worker(expr, line_number))

                # Collect remaining active workers
                while active_workers:
                    self._collect_finished_workers(active_workers, f_out)

                # Send results back to client
                try:
                    conn.sendall(self.output_file.read_bytes())
                    logger.info("✉️ Results sent to client")
                except OSError as exc:
                    logger.error(f"🔌❌ Client disconnected before receiving results: {exc}")
