"""Unit tests for WorkerProcess using real Pipe connections."""
from multiprocessing import Pipe

import pytest

from arithmetic_client_server.server.worker import WorkerProcess


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("2 + 3", 5.0),
        ("10 - 4", 6.0),
        ("3 * 4", 12.0),
        ("8 / 2", 4.0),
    ],
)
def test_worker_sends_result_for_valid_expression(expr: str, expected: float) -> None:
    """Worker sends computed result through the connection for valid expressions."""
    parent_conn, child_conn = Pipe()
    worker = WorkerProcess(conn=child_conn, expression=expr, line_number=1)
    worker.run()

    msg = parent_conn.recv()
    assert msg["line"] == 1
    assert msg["expression"] == expr
    assert msg["result"] == expected
    assert "error" not in msg


@pytest.mark.parametrize(
    "expr",
    [
        "2 +",         # Trailing operator
        "+ 3 4",       # Leading operator
        "3 4 + 5",     # Extra operand remaining
    ],
)
def test_worker_sends_error_for_invalid_expression(expr: str) -> None:
    """Worker sends an error message for malformed arithmetic expressions."""
    parent_conn, child_conn = Pipe()
    worker = WorkerProcess(conn=child_conn, expression=expr, line_number=2)
    worker.run()

    msg = parent_conn.recv()
    assert msg["line"] == 2
    assert msg["expression"] == expr
    assert "error" in msg
    assert isinstance(msg["error"], str)


def test_worker_rejects_empty_expression() -> None:
    """Pydantic validation prevents creating WorkerProcess with empty expression."""
    _, child_conn = Pipe()
    with pytest.raises(ValueError):
        WorkerProcess(conn=child_conn, expression="", line_number=1)
