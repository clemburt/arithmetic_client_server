from pydantic import BaseModel


class OperationRequest(BaseModel):
    expression: str


class OperationResult(BaseModel):
    expression: str
    result: float