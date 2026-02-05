"""Execution engine for Firefly statements"""

from .parser import (
    STATUS_NEXT, STATUS_STOP, STATUS_REPEAT,
    parse_input_statement, parse_math_shortcut, parse_assignment,
    parse_output_statement, parse_if_statement, parse_while_block, parse_for_block
)
from .evaluator import evaluate_expression
from .utils import get_indent


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

    # OUTPUT - check before assignment so "out x = 5" isn't treated as assignment
    if line.startswith("out "):
        parsed = parse_output_statement(line)
        content = parsed[1]  # Second element of tuple ("output", content)
        # Sort by longest variable name first to avoid partial replacements
        for var in sorted(variables.keys(), key=len, reverse=True):
            val = variables[var]
            content = content.replace(f"<{var}>", str(val))
        if content.startswith("**") and content.endswith("**"):
            print("\033[1m" + content[2:-2] + "\033[0m")
        else:
            print(content)
        return STATUS_NEXT

    # ASSIGNMENT
    parsed = parse_assignment(line)
    if parsed:
        _, name, value = parsed
        result = evaluate_expression(value, variables)
        variables[name] = result if result is not None else value
        return STATUS_NEXT

    # IF/ELSE STATEMENTS - handled at interpreter level
    if line.startswith("if ") or line.startswith("else"):
        return STATUS_NEXT

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

    # Get the raw block lines (with indentation) from the original lines
    base_indent = get_indent(lines[start_pc])
    block_start = start_pc + 1
    block_end = next_pc
    raw_block = lines[block_start:block_end]

    while evaluate_expression(condition_str, variables):
        result = _execute_block(raw_block, variables, base_indent)
        if result == STATUS_STOP:
            return None
        if result == STATUS_REPEAT:
            continue

    return next_pc


def execute_for_block(lines, start_pc, variables):
    """Execute a for loop block.

    Args:
        lines: List of all lines in the file
        start_pc: Program counter at the for statement
        variables: Dictionary of variables

    Returns:
        Next program counter position or None if stopped
    """
    loop_var, iterable, block_lines_raw, next_pc = parse_for_block(lines, start_pc)

    # Evaluate the iterable expression (e.g., range(1, 5))
    try:
        iter_obj = eval(iterable, {}, variables)
    except Exception:
        iter_obj = []

    # Get the raw block lines (with indentation) from the original lines
    base_indent = get_indent(lines[start_pc])
    block_start = start_pc + 1
    block_end = next_pc
    raw_block = lines[block_start:block_end]

    for value in iter_obj:
        variables[loop_var] = value
        result = _execute_block(raw_block, variables, base_indent)
        if result == STATUS_STOP:
            return None

    return next_pc


def _collect_block(lines, start_pc):
    """Collect indented block lines starting after start_pc."""
    base_indent = get_indent(lines[start_pc])
    block_lines = []
    pc = start_pc + 1
    while pc < len(lines):
        nxt = lines[pc]
        if not nxt.strip():
            pc += 1
            continue
        indent = get_indent(nxt)
        if indent > base_indent:
            block_lines.append(nxt.strip())
            pc += 1
        else:
            break
    return block_lines, pc


def _execute_block(raw_lines, variables, parent_indent):
    """Execute a block of lines, handling nested if statements properly.

    Args:
        raw_lines: List of raw lines (with indentation)
        variables: Dictionary of variables
        parent_indent: The indentation level of the parent block

    Returns:
        STATUS_NEXT, STATUS_STOP, or STATUS_REPEAT
    """
    pc = 0
    while pc < len(raw_lines):
        line = raw_lines[pc]
        stripped = line.strip()

        if not stripped:
            pc += 1
            continue

        # Handle nested if statements
        if stripped.startswith("if "):
            result = _execute_nested_if(raw_lines, pc, variables)
            if result is None:
                return STATUS_STOP
            pc = result
        else:
            status = execute_line(stripped, variables)
            if status == STATUS_STOP:
                return STATUS_STOP
            if status == STATUS_REPEAT:
                return STATUS_REPEAT
            pc += 1

    return STATUS_NEXT


def _execute_nested_if(lines, start_pc, variables):
    """Execute a nested if/else chain within a block.

    Returns the next line index after the if chain, or None on stop.
    """
    pc = start_pc
    executed = False
    base_indent = get_indent(lines[start_pc])

    while pc < len(lines):
        line = lines[pc]
        stripped = line.strip()
        current_indent = get_indent(line)

        # Check if we've exited the if/else chain
        if pc > start_pc and current_indent <= base_indent and not stripped.startswith("else"):
            break

        # Handle 'if' statement
        if stripped.startswith("if ") and pc == start_pc:
            _, condition, inline_action = parse_if_statement(stripped)

            # Collect nested block
            nested_block = []
            block_pc = pc + 1
            while block_pc < len(lines):
                next_line = lines[block_pc]
                if not next_line.strip():
                    block_pc += 1
                    continue
                if get_indent(next_line) > base_indent:
                    nested_block.append(next_line)
                    block_pc += 1
                else:
                    break

            if evaluate_expression(condition, variables):
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in nested_block:
                        status = execute_line(bl.strip(), variables)
                        if status == STATUS_STOP:
                            return None
            pc = block_pc

        # Handle 'else if' statement
        elif stripped.startswith("else if "):
            _, condition, inline_action = parse_if_statement("if " + stripped[8:])

            # Collect nested block
            nested_block = []
            block_pc = pc + 1
            while block_pc < len(lines):
                next_line = lines[block_pc]
                if not next_line.strip():
                    block_pc += 1
                    continue
                if get_indent(next_line) > base_indent:
                    nested_block.append(next_line)
                    block_pc += 1
                else:
                    break

            if not executed and evaluate_expression(condition, variables):
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in nested_block:
                        status = execute_line(bl.strip(), variables)
                        if status == STATUS_STOP:
                            return None
            pc = block_pc

        # Handle plain 'else'
        elif stripped == "else" or stripped.startswith("else do"):
            inline_action = ""
            if stripped.startswith("else do"):
                inline_action = stripped[8:].strip()

            # Collect nested block
            nested_block = []
            block_pc = pc + 1
            while block_pc < len(lines):
                next_line = lines[block_pc]
                if not next_line.strip():
                    block_pc += 1
                    continue
                if get_indent(next_line) > base_indent:
                    nested_block.append(next_line)
                    block_pc += 1
                else:
                    break

            if not executed:
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in nested_block:
                        status = execute_line(bl.strip(), variables)
                        if status == STATUS_STOP:
                            return None
            pc = block_pc

        else:
            break

    return pc


def execute_if_block(lines, start_pc, variables):
    """Execute an if/else-if/else chain starting at start_pc.

    Returns the next program counter after the chain, or None on stop.
    """
    pc = start_pc
    executed = False  # Track if any branch has executed

    while pc < len(lines):
        line = lines[pc].strip()

        # Handle 'if' statement
        if line.startswith("if ") and pc == start_pc:
            _, condition, inline_action = parse_if_statement(line)
            block_lines, next_pc = _collect_block(lines, pc)

            if evaluate_expression(condition, variables):
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in block_lines:
                        status = execute_line(bl, variables)
                        if status == STATUS_STOP:
                            return None
            pc = next_pc

        # Handle 'else if' statement
        elif line.startswith("else if "):
            # Parse as if statement (remove "else " prefix)
            _, condition, inline_action = parse_if_statement("if " + line[8:])
            block_lines, next_pc = _collect_block(lines, pc)

            if not executed and evaluate_expression(condition, variables):
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in block_lines:
                        status = execute_line(bl, variables)
                        if status == STATUS_STOP:
                            return None
            pc = next_pc

        # Handle 'else' statement (without condition)
        elif line == "else" or line.startswith("else do"):
            inline_action = ""
            if line.startswith("else do"):
                inline_action = line[8:].strip()
            block_lines, next_pc = _collect_block(lines, pc)

            if not executed:
                executed = True
                if inline_action:
                    status = execute_line(inline_action, variables)
                    if status == STATUS_STOP:
                        return None
                else:
                    for bl in block_lines:
                        status = execute_line(bl, variables)
                        if status == STATUS_STOP:
                            return None
            pc = next_pc

        else:
            # Not part of if/else chain, exit
            break

    return pc
