"""Calculator tool for safe mathematical expression evaluation.

This tool enables agents to perform financial calculations, unit economics,
valuation models, and other mathematical operations.
"""

import ast
import operator
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult


class CalculatorTool(BaseTool):
    """Safe mathematical expression evaluator.

    Uses Python's AST module to safely evaluate mathematical expressions
    without executing arbitrary code. Supports:
    - Basic arithmetic: +, -, *, /
    - Exponentiation: **
    - Parentheses for grouping
    - Negative numbers

    Common use cases:
    - Valuation calculations
    - Runway calculations (burn rate * months)
    - Unit economics (LTV/CAC ratios)
    - Market sizing (TAM/SAM/SOM)
    - Financial projections
    """

    # Supported operators mapping
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="calculator",
            description=(
                "Evaluate mathematical expressions safely. Supports basic arithmetic "
                "(+, -, *, /), exponentiation (**), modulo (%), floor division (//), "
                "and parentheses. Use for valuations, runway calculations, unit economics, "
                "market sizing, financial projections, and other mathematical operations. "
                "Examples: '(100000 * 12) / 10000', '50000 ** 2', '500000 / (50000 * 18)'"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "Mathematical expression to evaluate. Use standard operators: "
                            "+, -, *, /, **, %, //, and parentheses (). "
                            "Example: '(revenue * 12) / burn_rate' where you substitute actual numbers."
                        )
                    }
                },
                "required": ["expression"]
            }
        )

    def _eval_node(self, node: ast.AST) -> float:
        """Recursively evaluate an AST node.

        Args:
            node: AST node to evaluate

        Returns:
            Numeric result

        Raises:
            TypeError: If node type is not supported
            ZeroDivisionError: If division by zero
        """
        if isinstance(node, ast.Num):  # Number
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+ constant
            return node.value
        elif isinstance(node, ast.BinOp):  # Binary operation
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type not in self.OPERATORS:
                raise TypeError(f"Unsupported operator: {op_type.__name__}")

            return self.OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):  # Unary operation (like -5)
            operand = self._eval_node(node.operand)
            op_type = type(node.op)

            if op_type not in self.OPERATORS:
                raise TypeError(f"Unsupported unary operator: {op_type.__name__}")

            return self.OPERATORS[op_type](operand)
        else:
            raise TypeError(f"Unsupported AST node type: {type(node).__name__}")

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        """Execute a mathematical calculation.

        Args:
            expression: Mathematical expression to evaluate
            **kwargs: Additional context (unused)

        Returns:
            ToolResult with the calculation result
        """
        # Clean up the expression
        expression = expression.strip()

        if not expression:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error="Empty expression provided",
                result=None
            )

        try:
            # Parse the expression into an AST
            parsed = ast.parse(expression, mode='eval')

            # Evaluate the AST
            result = self._eval_node(parsed.body)

            # Format result nicely
            if isinstance(result, float):
                # Round to reasonable precision
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 6)

            return ToolResult(
                tool_name="calculator",
                success=True,
                result=result,
                metadata={
                    "expression": expression,
                    "result_type": type(result).__name__
                }
            )

        except ZeroDivisionError:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error="Division by zero is not allowed",
                result=None
            )

        except SyntaxError as e:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error=f"Invalid mathematical expression: {str(e)}",
                result=None
            )

        except TypeError as e:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error=f"Unsupported operation: {str(e)}. Only basic arithmetic is supported.",
                result=None
            )

        except Exception as e:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error=f"Calculation error: {str(e)}",
                result=None
            )


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(CalculatorTool())
