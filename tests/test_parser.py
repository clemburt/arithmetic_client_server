"""
Test class ExpressionParser
"""
from arithmetic_client_server.common.parser import ExpressionParser


def test_expression() -> None:
    assert ExpressionParser.evaluate("3 + 5 * 2") == 13

def test_complex_expression() -> None:
    expr = "38 - 83 - 52 + 30 - 24 - 89 / 66 + 18 / 7 * 77"
    result = ExpressionParser.evaluate(expr)
    assert isinstance(result, float)
