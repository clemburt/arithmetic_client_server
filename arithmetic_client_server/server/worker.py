from multiprocessing.connection import Connection
from arithmetic_client_server.common.parser import ExpressionParser
from arithmetic_client_server.common.logger import logger


class WorkerProcess:
    """
    Worker process computing a single arithmetic expression.

    Lifecycle:
    - Spawned by the parent server process
    - Receives one expression only
    - Sends the computed result through a Pipe
    - Terminates immediately after computation
    """

    def __init__(self, conn: Connection, expression: str, line_number: int):
        self.conn = conn
        self.expression = expression
        self.line_number = line_number

    def run(self) -> None:
        logger.info(f"Worker started (line {self.line_number})")

        try:
            result = ExpressionParser.evaluate(self.expression)
            self.conn.send(
                {
                    "line": self.line_number,
                    "expression": self.expression,
                    "result": result,
                }
            )
        except Exception as exc:
            logger.error(f"Worker failed (line {self.line_number})")
            self.conn.send(
                {
                    "line": self.line_number,
                    "expression": self.expression,
                    "error": str(exc),
                }
            )
        finally:
            self.conn.close()
            logger.info(f"Worker finished (line {self.line_number})")
