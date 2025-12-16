"""Test class ExpressionParser."""

import pytest

from arithmetic_client_server.common.parser import ExpressionParser


def test_tokenize_basic():
    """Tokenize splits a simple expression into correct tokens."""
    expr = "3 + 4 * 2"
    tokens = ExpressionParser.tokenize(expr)
    assert tokens == ["3", "+", "4", "*", "2"]


@pytest.mark.parametrize("token,expected", [
    ("123", True),
    ("45.67", True),
    ("-8.9", True),
    ("abc", False),
    ("+", False),
])
def test_is_number_true(token, expected):
    """_is_number correctly identifies numbers."""
    assert ExpressionParser._is_number(token) == expected


def test_to_rpn_basic():
    """to_rpn converts tokens to correct Reverse Polish Notation."""
    tokens = ["3", "+", "4", "*", "2"]
    rpn = ExpressionParser.to_rpn(tokens)
    # Numbers in order, operators according to precedence
    assert rpn == ["3", "4", "2", "*", "+"]


@pytest.mark.parametrize("expr,expected", [
    ("3 + 4", 7.0),
    ("10 - 2", 8.0),
    ("3 * 5", 15.0),
    ("8 / 2", 4.0),
    ("3 + 4 * 2", 11.0),  # tests precedence
    ("7 + 3 * 2 - 4 / 2", 11.0),
])
def test_evaluate_valid(expr, expected):
    """Evaluate returns correct result for valid expressions."""
    result = ExpressionParser.evaluate(expr)
    assert result == expected


@pytest.mark.parametrize("expr", [
    "3 +",        # Trailing operator
    "+ 3 4",      # Leading operator
    "3 *",        # Single number with trailing operator
    "3 4 + 5",    # Extra operand remaining
    "",           # Empty expression
])
def test_evaluate_invalid_expression(expr):
    """Evaluate raises ValueError for malformed expressions."""
    with pytest.raises(ValueError):
        ExpressionParser.evaluate(expr)


@pytest.mark.parametrize("expr,expected", [
    ("3 + 4", ["3", "4", "+"]),
    ("3 + 4 * 2", ["3", "4", "2", "*", "+"]),
    ("10 / 2 - 1", ["10", "2", "/", "1", "-"]),
])
def test_to_rpn_various(expr, expected):
    """to_rpn handles multiple expressions correctly."""
    tokens = ExpressionParser.tokenize(expr)
    rpn = ExpressionParser.to_rpn(tokens)
    assert rpn == expected
