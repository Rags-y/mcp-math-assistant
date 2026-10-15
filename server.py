
import math

from mcp.server.fastmcp import FastMCP

# Create our MCP server
mcp = FastMCP("MCP Math Assistant")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise a number to a power."""
    result = base**exponent

    if isinstance(result, complex):
        raise ValueError("This calculator supports real results only.")

    if not math.isfinite(result):
        raise ValueError("The result is too large or not finite.")

    return result


@mcp.tool()
def square_root(number: float) -> float:
    """Calculate the square root of a non-negative number."""
    if number < 0:
        raise ValueError("Cannot calculate the real square root of a negative number.")

    return math.sqrt(number)


@mcp.tool()
def modulo(a: float, b: float) -> float:
    """Return the remainder after dividing a by b."""
    if b == 0:
        raise ValueError("Cannot calculate a remainder with a zero divisor.")

    return a % b


if __name__ == "__main__":
    mcp.run()
