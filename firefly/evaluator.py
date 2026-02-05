"""Expression evaluation for the Firefly interpreter"""

from .errors import FireflyRuntimeError, FireflyTypeError, FireflyVariableError


def evaluate_expression(expr, variables, line_number=None):
    """
    Evaluate a Firefly expression with variable substitution.

    Args:
        expr: The expression string to evaluate
        variables: Dictionary of variable values
        line_number: Optional line number for error reporting

    Returns:
        The result of the expression

    Raises:
        FireflyRuntimeError: If expression evaluation fails
        FireflyTypeError: If the result is an unsupported type
    """
    if not expr or not isinstance(expr, str):
        raise FireflyTypeError(f"Invalid expression: {expr}", line_number)

    original_expr = expr

    #Replace variables (Longest names first to avoid partial matches)
    for var in sorted(variables.keys(), key=len, reverse=True):
        if var in expr:
            val = str(variables[var])
            expr = expr.replace(var, val)

     #Fix Logic Syntax (single = becomes == for comparison)
    if "=" in expr and "==" not in expr and "<=" not in expr and ">=" not in expr:
        expr = expr.replace("=", "==")

    try:
        #Evaluate with no builtins
        result = eval(expr, {"__builtins__": {}}, {})
        #Only allow simple types (int, float, str, bool) to be returned
        if isinstance(result, (int, float, str, bool)):
            return result
        raise FireflyTypeError(
            f"Expression '{original_expr}' resulted in unsupported type: {type(result).__name__}",
            line_number
        )
    except SyntaxError as e:
        raise FireflyRuntimeError(
            f"Syntax error in expression '{original_expr}': {str(e)}",
            line_number
        )
    except NameError as e:
        # Extract variable name from error message
        var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        raise FireflyVariableError(
            f"Undefined variable '{var_name}' in expression '{original_expr}'",
            line_number
        )
    except ZeroDivisionError:
        raise FireflyRuntimeError(
            f"Division by zero in expression '{original_expr}'",
            line_number
        )
    except (TypeError, ValueError) as e:
        raise FireflyRuntimeError(
            f"Error evaluating expression '{original_expr}': {str(e)}",
            line_number
        )
    except Exception as e:
        raise FireflyRuntimeError(
            f"Unexpected error evaluating expression '{original_expr}': {str(e)}",
            line_number
        )
