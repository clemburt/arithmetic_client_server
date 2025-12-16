"""Pydantic models for arithmetic operation requests and results."""
from pydantic import BaseModel, Field


class OperationRequest(BaseModel):
    """Represents a single arithmetic operation request sent to the server."""
    
    expression: str = Field(..., description="Arithmetic expression as a string")

class OperationResult(BaseModel):
    """Represents the result of an evaluated arithmetic operation."""

    expression: str = Field(..., description="Original arithmetic expression")
    result: float = Field(..., description="Evaluated numeric result of the expression")
