"""Worker process for evaluating arithmetic expressions."""
from multiprocessing.connection import Connection
from typing import Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arithmetic_client_server.common.logger import logger
from arithmetic_client_server.common.parser import ExpressionParser


class WorkerProcess(BaseModel):
    """
    Worker process responsible for evaluating a single arithmetic expression.

    Lifecycle:
        - Spawned by the parent server process
        - Receives one expression only
        - Sends the computed result or error through a Pipe
        - Terminates immediately after computation
    """

    # Make the Pydantic instance immutable (read-only) for safety
    # Allow arbitrary types like multiprocessing.Connection
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    conn: Connection = Field(..., description="Connection object for sending results back to server")
    expression: str = Field(..., description="Single arithmetic expression to evaluate")
    line_number: int = Field(..., ge=1, description="Line number in the input file")

    @field_validator("expression")
    def expression_must_not_be_empty(cls, v: str) -> str:
        """Ensure that the expression is not empty."""
        if not v.strip():
            raise ValueError("Expression cannot be empty")
        return v

    def run(self) -> None:
        """
        Evaluate the arithmetic expression and send the result or error through the pipe.

        :return: None
        """
        logger.info(f"👷🏁 Worker started on line {self.line_number}: {self.expression}")

        result: Union[float, None] = None

        try:
            # Evaluate expression safely
            result = ExpressionParser.evaluate(self.expression)

            # Send result through the connection
            self.conn.send(
                {
                    "line": self.line_number,
                    "expression": self.expression,
                    "result": result,
                }
            )

        except Exception as exc:
            logger.error(
                f"👷❌ Worker failed on line {self.line_number}: {exc}\n" \
                f"Invalid arithmetic expression, could not evaluate: {self.expression!r}"
            )
            
            # Send error through the connection
            self.conn.send(
                {
                    "line": self.line_number,
                    "expression": self.expression,
                    "error": str(exc),
                }
            )

        finally:
            # Always close the connection
            self.conn.close()

            if result is not None:
                logger.info(f"👷✅ Worker finished on line {self.line_number}: {result}")
