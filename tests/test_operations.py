"""Test classes OperationRequest and OperationResult."""
from pydantic import ValidationError
import pytest

from arithmetic_client_server.common.operations import OperationRequest, OperationResult


def test_operation_request_valid() -> None:
    """Test that a valid OperationRequest can be created."""
    req = OperationRequest(expression="2 + 2 * 3")
    assert req.expression == "2 + 2 * 3"
    assert isinstance(req.expression, str)

def test_operation_request_invalid_type() -> None:
    """Test that non-string expressions raise a validation error."""
    with pytest.raises(ValidationError):
        # int instead of str
        OperationRequest(expression=123)

def test_operation_result_valid() -> None:
    """Test that a valid OperationResult can be created."""
    res = OperationResult(expression="2 + 2 * 3", result=8.0)
    assert res.expression == "2 + 2 * 3"
    assert res.result == 8.0
    assert isinstance(res.result, float)

def test_operation_result_invalid_expression_type() -> None:
    """Test that invalid expression type raises a validation error."""
    with pytest.raises(ValidationError):
        OperationResult(expression=42, result=8.0)

def test_operation_result_invalid_result_type() -> None:
    """Test that invalid result type raises a validation error."""
    with pytest.raises(ValidationError):
        OperationResult(expression="2 + 2", result="not a float")
