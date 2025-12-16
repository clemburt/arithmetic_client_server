import operator
from typing import List, Callable


OperatorFn = Callable[[float, float], float]

OPERATORS: dict[str, tuple[int, OperatorFn]] = {
    "+": (1, operator.add),
    "-": (1, operator.sub),
    "*": (2, operator.mul),
    "/": (2, operator.truediv),
}


class ExpressionParser:
    """
    Utility class responsible for parsing and evaluating arithmetic operations.

    Design constraints:
    - No usage of eval()
    - No dynamic code execution
    - Safe, deterministic computation

    Algorithm:
    - Tokenization based on whitespace
    - Shunting-yard algorithm to produce Reverse Polish Notation (RPN)
    - Stack-based RPN evaluation
    """

    @staticmethod
    def tokenize(expr: str) -> List[str]:
        """
        Split an expression into tokens.

        Parameters
        ----------
        expr : str
            Arithmetic expression (tokens must be space-separated).

        Returns
        -------
        List[str]
            List of tokens.
        """
        return expr.split()

    @staticmethod
    def _is_number(token: str) -> bool:
        """
        Check if a token represents a valid number.

        Supports integers and floating-point values.
        """
        try:
            float(token)
            return True
        except ValueError:
            return False

    @staticmethod
    def to_rpn(tokens: List[str]) -> List[str]:
        """
        Convert a list of tokens into Reverse Polish Notation (RPN)
        using the Shunting-yard algorithm.
        """
        output, stack = [], []

        for token in tokens:
            if ExpressionParser._is_number(token):
                output.append(token)
            else:
                prec = OPERATORS[token][0]
                while stack and OPERATORS.get(stack[-1], (0,))[0] >= prec:
                    output.append(stack.pop())
                stack.append(token)
        # append remaining operators without reversing
        output.extend(stack[::-1])
        return output

    @staticmethod
    def evaluate(expr: str) -> float:
        """
        Evaluate an arithmetic expression safely.

        Parameters
        ----------
        expr : str
            Arithmetic expression.

        Returns
        -------
        float
            Computed result.

        Raises
        ------
        ValueError
            If the expression is invalid.
        """
        tokens = ExpressionParser.tokenize(expr)
        rpn = ExpressionParser.to_rpn(tokens)
        stack = []
        for token in rpn:
            if token.isdigit():
                stack.append(float(token))
            else:
                if len(stack) < 2:
                    raise ValueError(f"Invalid expression (not enough operands): {expr}")
                b, a = stack.pop(), stack.pop()
                stack.append(OPERATORS[token][1](a, b))
        if len(stack) != 1:
            raise ValueError(f"Invalid expression (remaining operands): {expr}")
        return stack[0]
