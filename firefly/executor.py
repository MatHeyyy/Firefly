"""Execution engine for Firefly statements"""

from .parser import (
    STATUS_NEXT, STATUS_STOP, STATUS_REPEAT,
    parse_input_statement, parse_math_shortcut, parse_assignment,
    parse_output_statement, parse_if_statement, parse_while_block
)
from .evaluator import evaluate_expression


def execute_line(line, variables):
    """
    Execute a single Firefly line.

    Args:
        line: The line to execute
        variables: Dictionary of variables to update

    Returns:
        STATUS_NEXT, STATUS_STOP, or STATUS_REPEAT
    """
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith("#"):
        return STATUS_NEXT

    # Stop and repeat keywords
    if line == "stop":
        return STATUS_STOP
    if line == "repeat":
        return STATUS_REPEAT

    # INPUT
    if line.startswith("in "):
        parsed = parse_input_statement(line)
        if parsed:
            _, var_name, prompt = parsed
            val = input(prompt + " ")
            try:
                variables[var_name] = int(val)
            except:
                variables[var_name] = val
        return STATUS_NEXT

    # MATH SHORTCUTS
    parsed = parse_math_shortcut(line)
    if parsed:
        _, var, op, val = parsed
        return execute_line(f"{var} = {var} {op} {val}", variables)

    # ASSIGNMENT
    parsed = parse_assignment(line)
    if parsed:
        _, name, value = parsed
        result = evaluate_expression(value, variables)
        variables[name] = result if result is not None else value
        return STATUS_NEXT

    # OUTPUT
    if line.startswith("out "):
        parsed = parse_output_statement(line)
        content = parsed[1]  # Second element of tuple ("output", content)
        for var, val in variables.items():
            content = content.replace(f"<{var}>", str(val))
        if content.startswith("**") and content.endswith("**"):
            print("\033[1m" + content[2:-2] + "\033[0m")
        else:
            print(content)
        return STATUS_NEXT

    # IF STATEMENTS
    if line.startswith("if "):
        _, condition, action = parse_if_statement(line)
        if evaluate_expression(condition, variables):
            return execute_line(action, variables) if action else STATUS_NEXT

    return STATUS_NEXT


def execute_while_block(lines, start_pc, variables):
    """
    Execute a while loop block.

    Args:
        lines: List of all lines in the file
        start_pc: Program counter at the while statement
        variables: Dictionary of variables

    Returns:
        Next program counter position or None if stopped
    """
    condition_str, block_lines, next_pc = parse_while_block(lines, start_pc)

    while evaluate_expression(condition_str, variables):
        for bl in block_lines:
            status = execute_line(bl, variables)
            if status == STATUS_STOP:
                return None
            if status == STATUS_REPEAT:
                break

    return next_pc
