"""Parse and evaluate arithmetic operations safely."""
from collections.abc import Callable as ABCCallable
import operator
from typing import Callable, List, Tuple


# Type alias for operator functions (taking two floats, returning a float)
OperatorFn: ABCCallable[[float, float], float] = Callable[[float, float], float]

# Mapping of operator symbols to (precedence, function)
OPERATORS: dict[str, Tuple[int, OperatorFn]] = {
    "+": (1, operator.add),
    "-": (1, operator.sub),
    "*": (2, operator.mul),
    "/": (2, operator.truediv),
}


class ExpressionParser:
    """
    Parse and evaluate arithmetic expressions safely.

    Design constraints:
        - No eval(), no dynamic code execution
        - Safe, deterministic computation

    Algorithm:
        1. Tokenize based on whitespace
        2. Convert to Reverse Polish Notation (RPN) using Shunting-yard
        3. Evaluate RPN using a stack

    The Shunting-yard algorithm converts an infix expression into Reverse Polish Notation (RPN), allowing safe, stack-based evaluation without parentheses.
    It handles operator precedence by temporarily storing operators on a stack and outputting them in the correct order.

    Examples:
        - Infix expression (standard notation): 3 + 4 * 2
        - Corresponding Reverse Polish Notation (RPN): 3 4 2 * +

    """

    @staticmethod
    def tokenize(expr: str) -> List[str]:
        """
        Split an arithmetic expression into tokens.

        Tokens must be space-separated (e.g., "3 + 4 * 2").

        :param str expr: Arithmetic expression as a string

        :return: List of tokens
        :rtype: List[str]
        """
        # Simply split by whitespace
        return expr.split()

    @staticmethod
    def _is_number(token: str) -> bool:
        """
        Determine if a token represents a numeric value.

        Supports both integers and floating-point numbers.

        :param str token: Token string

        :return: True if token can be converted to float, else False
        :rtype: bool
        """
        try:
            float(token)
            return True
        except ValueError:
            return False

    @staticmethod
    def to_rpn(tokens: List[str]) -> List[str]:
        """
        Convert a list of tokens into Reverse Polish Notation (RPN) using the Shunting-yard algorithm.

        :param List[str] tokens: List of arithmetic tokens
        
        :return: List of tokens in RPN order
        :rtype: List[str]
        """
        output: List[str] = []
        stack: List[str] = []

        for token in tokens:
            if ExpressionParser._is_number(token):
                # Numbers are added directly to the output
                output.append(token)
            else:
                # Operator: pop operators from stack with higher or equal precedence
                prec = OPERATORS[token][0]
                while stack and OPERATORS.get(stack[-1], (0,))[0] >= prec:
                    output.append(stack.pop())
                stack.append(token)

        # Append remaining operators in reverse order (stack top first)
        output.extend(stack[::-1])
        return output

    @staticmethod
    def evaluate(expr: str) -> float:
        """
        Evaluate an arithmetic expression safely.

        :param str expr: Arithmetic expression string

        :return: Computed result as float
        :rtype: float
        :raises ValueError: If expression is invalid or malformed
        """
        # Tokenize the expression
        tokens: List[str] = ExpressionParser.tokenize(expr)
        
        if not tokens:
            raise ValueError("Empty expression")

        # Check that the first and last tokens are not operators
        if tokens[0] in OPERATORS or tokens[-1] in OPERATORS:
            raise ValueError(f"Expression cannot start or end with an operator: {expr}")

        # Convert to RPN
        rpn: List[str] = ExpressionParser.to_rpn(tokens)

        # Evaluate RPN using a stack
        stack: List[float] = []
        for token in rpn:
            if ExpressionParser._is_number(token):
                stack.append(float(token))
            else:
                # Operator requires two operands
                if len(stack) < 2:
                    raise ValueError(f"Invalid expression (not enough operands): {expr}")
                b: float = stack.pop()
                a: float = stack.pop()
                stack.append(OPERATORS[token][1](a, b))

        if len(stack) != 1:
            raise ValueError(f"Invalid expression (remaining operands): {expr}")

        return stack[0]
