"""Expression evaluation for the Firefly interpreter"""

from .errors import FireflyRuntimeError, FireflyTypeError, FireflyVariableError

# Safe builtins allowed in expressions
SAFE_BUILTINS = {
    "range": range,
    "len": len,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "True": True,
    "False": False,
}


def _safe_eval(expr: str, variables: dict, line_number=None):
    if not expr or not isinstance(expr, str):
        raise FireflyTypeError(f"Invalid expression: {expr}", line_number)

    try:
        return eval(expr, {"__builtins__": SAFE_BUILTINS}, dict(variables))
    except SyntaxError as e:
        raise FireflyRuntimeError(f"Syntax error in expression '{expr}': {e}", line_number)
    except NameError as e:
        msg = str(e)
        var_name = msg.split("'")[1] if "'" in msg else "unknown"
        raise FireflyVariableError(f"Undefined variable '{var_name}' in expression '{expr}'", line_number)
    except ZeroDivisionError:
        raise FireflyRuntimeError(f"Division by zero in expression '{expr}'", line_number)
    except (TypeError, ValueError) as e:
        raise FireflyRuntimeError(f"Error evaluating expression '{expr}': {e}", line_number)
    except Exception as e:
        raise FireflyRuntimeError(f"Unexpected error evaluating expression '{expr}': {e}", line_number)


def evaluate_expression(expr, variables, line_number=None):
    original_expr = expr
    result = _safe_eval(expr, variables, line_number)

    if isinstance(result, (int, float, str, bool)):
        return result

    raise FireflyTypeError(
        f"Expression '{original_expr}' resulted in unsupported type: {type(result).__name__}",
        line_number
    )


def evaluate_iterable(iterable_expr, variables, line_number=None):
    original_expr = iterable_expr
    result = _safe_eval(iterable_expr, variables, line_number)

    try:
        iter(result)
        return result
    except TypeError:
        raise FireflyRuntimeError(f"'{original_expr}' is not iterable in for loop", line_number)

