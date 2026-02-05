"""Expression evaluation for the Firefly interpreter"""


def evaluate_expression(expr, variables):
    """
    Evaluate a Firefly expression with variable substitution.

    Args:
        expr: The expression string to evaluate
        variables: Dictionary of variable values

    Returns:
        The result of the expression, or None if evaluation fails
    """
    # 1. Replace variables (Longest names first to avoid partial matches)
    for var in sorted(variables.keys(), key=len, reverse=True):
        if var in expr:
            val = str(variables[var])
            expr = expr.replace(var, val)

    # 2. Fix Logic Syntax (single = becomes == for comparison)
    if "=" in expr and "==" not in expr and "<=" not in expr and ">=" not in expr:
        expr = expr.replace("=", "==")

    try:
        return eval(expr)
    except:
        return None
