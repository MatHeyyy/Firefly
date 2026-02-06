"""Execution engine for Firefly statements"""

import re
from .parser import (
    STATUS_NEXT, STATUS_STOP, STATUS_REPEAT, STATUS_RETURN,
    parse_input_statement, parse_math_shortcut, parse_assignment,
    parse_output_statement, parse_if_statement, parse_while_block, parse_for_block,
    parse_function_definition, parse_function_call
)
from .evaluator import evaluate_expression, evaluate_iterable
from .utils import get_indent
from .errors import FireflyRuntimeError, FireflyVariableError, FireflySyntaxError


def execute_line(line, variables, line_number=None, functions=None):
    """
    Execute a single Firefly line.

    Args:
        line: The line to execute
        variables: Dictionary of variables to update
        line_number: Optional line number for error reporting
        functions: Dictionary of user-defined functions

    Returns:
        STATUS_NEXT, STATUS_STOP, STATUS_RETURN or STATUS_REPEAT

    Raises:
        FireflyRuntimeError: If execution fails
        FireflySyntaxError: If the syntax is invalid
    """
    if functions is None:
        functions = {}

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
        try:
            parsed = parse_input_statement(line)
            if parsed:
                _, var_name, prompt = parsed
                val = input(prompt + " ")
                try:
                    variables[var_name] = int(val)
                except ValueError:
                    variables[var_name] = val
        except (FireflySyntaxError, EOFError) as e:
            if isinstance(e, EOFError):
                raise FireflyRuntimeError("Unexpected end of input", line_number)
            raise
        return STATUS_NEXT

    # MATH SHORTCUTS
    parsed = parse_math_shortcut(line)
    if parsed:
        _, var, op, val = parsed
        if var not in variables:
            raise FireflyVariableError(f"Variable '{var}' is not defined", line_number)
        return execute_line(f"{var} = {var} {op} {val}", variables, line_number)

    # OUTPUT - check before assignment so "out x = 5" isn't treated as assignment
    if line.startswith("out "):
        try:
            parsed = parse_output_statement(line)
            content = parsed[1]  # Second element of tuple
            apply_styling = parsed[2] if len(parsed) > 2 else False  # Third element indicates styling

            # Sort by longest variable name first to avoid partial replacements
            for var in sorted(variables.keys(), key=len, reverse=True):
                val = variables[var]
                content = content.replace(f"<{var}>", str(val))

            # Check for undefined variables (remaining <...> patterns)
            undefined_vars = re.findall(r'<([^>]+)>', content)
            if undefined_vars:
                raise FireflyVariableError(
                    f"Undefined variable '{undefined_vars[0]}' in output statement",
                    line_number
                )

            # Apply styling if requested
            if apply_styling:
                # Process inline styling markers

                # Replace **text** with bold
                content = re.sub(r'\*\*(.+?)\*\*', r'\033[1m\1\033[22m', content)

                # Replace //text// with italic
                content = re.sub(r'//(.+?)//', r'\033[3m\1\033[23m', content)

                print(content)
            else:
                # Plain output without styling
                print(content)
        except Exception as e:
            if not isinstance(e, (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError)):
                raise FireflyRuntimeError(f"Error in output statement: {str(e)}", line_number)
            raise

        return STATUS_NEXT

    # RETURN STATEMENT
    if line.startswith("return "):
        # Grab the math logic after the word "return"
        expression = line[7:].strip()

        # Evaluate it
        value = evaluate_expression(expression, variables)

        # Return a special tuple
        return (STATUS_RETURN, value)

    # ASSIGNMENT
    parsed = parse_assignment(line)
    if parsed:
        _, name, value = parsed
        try:
            # Check if the right-hand side is a function call (contains " with " or ends with just function name)
            if " with " in value or (value in functions if functions else False):
                # Parse as function call
                func_name, arg_values = parse_function_call(value)
                if func_name in (functions or {}):
                    result = execute_function(func_name, arg_values, functions, variables, line_number)
                    variables[name] = result
                else:
                    # Not a known function, try regular expression
                    result = evaluate_expression(value, variables, line_number)
                    variables[name] = result if result is not None else value
            else:
                result = evaluate_expression(value, variables, line_number)
                variables[name] = result if result is not None else value
        except (FireflyRuntimeError, FireflyVariableError) as e:
            # Re-raise with line number if not already set
            if e.line_number is None:
                e.line_number = line_number
            raise
        return STATUS_NEXT

    # IF/ELSE STATEMENTS - handled at interpreter level
    if line.startswith("if ") or line.startswith("else"):
        return STATUS_NEXT

    # FUNCTION DEFINITION - handled at interpreter level
    if line.startswith("function"):
        return STATUS_NEXT

    # FUNCTION CALL - Try to parse as function call if it looks like one
    # Check if it's a potential function call (not a known statement type)
    if not any(line.startswith(kw) for kw in ["in ", "out ", "if ", "while ", "for ", "else", "stop", "repeat"]) and \
       " = " not in line and " += " not in line and " -= " not in line:
        # Try to parse as function call
        func_name, arg_values = parse_function_call(line)
        if func_name in functions:
            execute_function(func_name, arg_values, functions, variables, line_number)
            return STATUS_NEXT

    # Unknown statement
    raise FireflySyntaxError(f"Unknown statement: '{line}'", line_number)


def execute_function(func_name, arg_values, functions, variables, line_number=None):
    """
    Execute a user-defined function.

    Args:
        func_name: Name of the function to execute
        arg_values: List of argument values (can be variable names or literals)
        functions: Dictionary of user-defined functions
        variables: Dictionary of variables
        line_number: Optional line number for error reporting

    Returns:
        None

    Raises:
        FireflyRuntimeError: If execution fails
    """
    if func_name not in functions:
        raise FireflyRuntimeError(f"Function '{func_name}' is not defined", line_number)

    func_def = functions[func_name]
    arg_names = func_def["args"]
    body_lines = func_def["body"]
    base_indent = func_def.get("base_indent", 0)

    # Validate argument count
    if len(arg_values) != len(arg_names):
        raise FireflyRuntimeError(
            f"Function '{func_name}' expects {len(arg_names)} argument(s), but {len(arg_values)} were provided",
            line_number
        )

    # Create a local scope by copying the current variables
    local_vars = variables.copy()

    # Evaluate and bind arguments
    for arg_name, arg_value in zip(arg_names, arg_values):
        arg_value = arg_value.strip()
        # Check if it's a string literal (quoted)
        if (arg_value.startswith('"') and arg_value.endswith('"')) or \
           (arg_value.startswith("'") and arg_value.endswith("'")):
            # Remove quotes and use as string literal
            local_vars[arg_name] = arg_value[1:-1]
        elif arg_value in variables:
            # It's a variable reference
            local_vars[arg_name] = variables[arg_value]
        else:
            # Try to evaluate it as an expression
            try:
                result = evaluate_expression(arg_value, variables, line_number)
                local_vars[arg_name] = result
            except (FireflyRuntimeError, FireflyVariableError):
                # If evaluation fails, treat it as a string literal
                local_vars[arg_name] = arg_value

    # Execute function body using _execute_block for proper control flow handling
    try:
        result = _execute_block(body_lines, local_vars, base_indent, line_number or 0, functions)
    except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
        if e.line_number is None:
            e.line_number = line_number
        raise

    # Update variables in the outer scope (for any modifications made inside the function)
    # This allows side effects but keeps local function parameters local
    for var in variables:
        if var in local_vars and var not in arg_names:
            variables[var] = local_vars[var]

    # Handle return value
    if isinstance(result, tuple) and result[0] == STATUS_RETURN:
        return result[1]

    return None


def execute_while_block(lines, start_pc, variables, functions=None):
    """
    Execute a while loop block.

    Args:
        lines: List of all lines in the file
        start_pc: Program counter at the while statement
        variables: Dictionary of variables
        functions: Dictionary of user-defined functions

    Returns:
        Next program counter position or None if stopped

    Raises:
        FireflyRuntimeError: If execution fails
        FireflySyntaxError: If the syntax is invalid
    """
    if functions is None:
        functions = {}

    try:
        condition_str, block_lines, next_pc = parse_while_block(lines, start_pc)
    except Exception as e:
        if not isinstance(e, (FireflyRuntimeError, FireflySyntaxError)):
            raise FireflySyntaxError(f"Error parsing while loop: {str(e)}", start_pc + 1)
        raise

    # Get the raw block lines (with indentation) from the original lines
    base_indent = get_indent(lines[start_pc])
    block_start = start_pc + 1
    block_end = next_pc
    raw_block = lines[block_start:block_end]

    if not raw_block:
        raise FireflySyntaxError("While loop has empty block", start_pc + 1)

    max_iterations = 100000  # Safety limit to prevent infinite loops
    iteration_count = 0

    try:
        while evaluate_expression(condition_str, variables, start_pc + 1):
            iteration_count += 1
            if iteration_count > max_iterations:
                raise FireflyRuntimeError(
                    f"While loop exceeded maximum iterations ({max_iterations}). Possible infinite loop.",
                    start_pc + 1
                )

            result = _execute_block(raw_block, variables, base_indent, block_start, functions)
            if result == STATUS_STOP:
                return None
            if result == STATUS_REPEAT:
                continue
    except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError):
        raise
    except Exception as e:
        raise FireflyRuntimeError(f"Error in while loop: {str(e)}", start_pc + 1)

    return next_pc


def execute_for_block(lines, start_pc, variables, functions=None):
    """Execute a for loop block.

    Args:
        lines: List of all lines in the file
        start_pc: Program counter at the for statement
        variables: Dictionary of variables
        functions: Dictionary of user-defined functions

    Returns:
        Next program counter position or None if stopped

    Raises:
        FireflyRuntimeError: If execution fails
        FireflySyntaxError: If the syntax is invalid
    """
    if functions is None:
        functions = {}

    try:
        loop_var, iterable, block_lines_raw, next_pc = parse_for_block(lines, start_pc)
    except Exception as e:
        if not isinstance(e, (FireflyRuntimeError, FireflySyntaxError)):
            raise FireflySyntaxError(f"Error parsing for loop: {str(e)}", start_pc + 1)
        raise

    # Evaluate the iterable expression (e.g., range(1, 5)) using safe evaluation
    iter_obj = evaluate_iterable(iterable, variables, start_pc + 1)

    # Get the raw block lines (with indentation) from the original lines
    base_indent = get_indent(lines[start_pc])
    block_start = start_pc + 1
    block_end = next_pc
    raw_block = lines[block_start:block_end]

    try:
        for value in iter_obj:
            variables[loop_var] = value
            result = _execute_block(raw_block, variables, base_indent, block_start, functions)
            if result == STATUS_STOP:
                return None
    except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError):
        raise
    except Exception as e:
        raise FireflyRuntimeError(f"Error in for loop: {str(e)}", start_pc + 1)

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


def _execute_block(raw_lines, variables, parent_indent, start_line_number=0, functions=None):
    """Execute a block of lines, handling nested if statements properly.

    Args:
        raw_lines: List of raw lines (with indentation)
        variables: Dictionary of variables
        parent_indent: The indentation level of the parent block
        start_line_number: Starting line number for error reporting
        functions: Dictionary of user-defined functions

    Returns:
        STATUS_NEXT, STATUS_STOP, STATUS_RETURN or STATUS_REPEAT

    Raises:
        FireflyRuntimeError: If execution fails
    """
    if functions is None:
        functions = {}

    pc = 0
    while pc < len(raw_lines):
        line = raw_lines[pc]
        stripped = line.strip()
        current_line_number = start_line_number + pc + 1

        if not stripped:
            pc += 1
            continue

        try:
            # Handle nested if statements
            if stripped.startswith("if "):
                result = _execute_nested_if(raw_lines, pc, variables, start_line_number, functions)
                if result is None:
                    return STATUS_STOP
                # Handle return statement from nested if
                if isinstance(result, tuple) and result[0] == STATUS_RETURN:
                    return result
                pc = result
            # Handle nested for loops
            elif stripped.startswith("for "):
                result = _execute_nested_for(raw_lines, pc, variables, start_line_number, functions)
                if result is None:
                    return STATUS_STOP
                # Handle return statement from nested for
                if isinstance(result, tuple) and result[0] == STATUS_RETURN:
                    return result
                pc = result
            # Handle nested while loops
            elif stripped.startswith("while "):
                result = _execute_nested_while(raw_lines, pc, variables, start_line_number, functions)
                if result is None:
                    return STATUS_STOP
                # Handle return statement from nested while
                if isinstance(result, tuple) and result[0] == STATUS_RETURN:
                    return result
                pc = result
            else:
                status = execute_line(stripped, variables, current_line_number, functions)
                if status == STATUS_STOP:
                    return STATUS_STOP
                if status == STATUS_REPEAT:
                    return STATUS_REPEAT
                # Handle return statement - propagate the tuple
                if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                    return status
                pc += 1
        except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
            # Re-raise with line number if not already set
            if e.line_number is None:
                e.line_number = current_line_number
            raise
        except Exception as e:
            raise FireflyRuntimeError(f"Unexpected error: {str(e)}", current_line_number)

    return STATUS_NEXT


def _execute_nested_if(lines, start_pc, variables, start_line_number=0, functions=None):
    """Execute a nested if/else chain within a block.

    Returns the next line index after the if chain, or None on stop.

    Raises:
        FireflyRuntimeError: If execution fails
    """
    if functions is None:
        functions = {}

    pc = start_pc
    executed = False
    base_indent = get_indent(lines[start_pc])

    while pc < len(lines):
        line = lines[pc]
        stripped = line.strip()
        current_indent = get_indent(line)
        current_line_number = start_line_number + pc + 1

        # Check if we've exited the if/else chain
        if pc > start_pc and current_indent <= base_indent and not stripped.startswith("else"):
            break

        try:
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

                if evaluate_expression(condition, variables, current_line_number):
                    executed = True
                    if inline_action:
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
                    elif nested_block:
                        status = _execute_block(nested_block, variables, base_indent, start_line_number + pc, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
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

                if not executed and evaluate_expression(condition, variables, current_line_number):
                    executed = True
                    if inline_action:
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
                    elif nested_block:
                        status = _execute_block(nested_block, variables, base_indent, start_line_number + pc, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
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
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
                    elif nested_block:
                        status = _execute_block(nested_block, variables, base_indent, start_line_number + pc, functions)
                        if status == STATUS_STOP:
                            return None
                        # Handle return statement
                        if isinstance(status, tuple) and status[0] == STATUS_RETURN:
                            return status
                pc = block_pc

            else:
                break
        except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
            if e.line_number is None:
                e.line_number = current_line_number
            raise
        except Exception as e:
            raise FireflyRuntimeError(f"Error in if statement: {str(e)}", current_line_number)

    return pc


def _execute_nested_for(lines, start_pc, variables, start_line_number=0, functions=None):
    """Execute a nested for loop within a block.

    Returns the next line index after the loop, or None on stop.

    Raises:
        FireflyRuntimeError: If execution fails
    """
    if functions is None:
        functions = {}

    line = lines[start_pc]
    stripped = line.strip()
    base_indent = get_indent(line)
    current_line_number = start_line_number + start_pc + 1

    try:
        # Parse the for loop
        from .parser import parse_for_block as parse_for_line
        # We need to reconstruct full lines for the parser
        temp_lines = [line]
        pc = start_pc + 1
        while pc < len(lines):
            temp_lines.append(lines[pc])
            pc += 1

        # Parse using the for block parser
        loop_var, iterable, _, _ = parse_for_line(temp_lines, 0)

        # Collect the nested block
        nested_block = []
        block_pc = start_pc + 1
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

        # Evaluate the iterable using safe evaluation
        iter_obj = evaluate_iterable(iterable, variables, current_line_number)

        # Execute the loop
        for value in iter_obj:
            variables[loop_var] = value
            result = _execute_block(nested_block, variables, base_indent, start_line_number + block_pc, functions)
            if result == STATUS_STOP:
                return None
            # Handle return statement
            if isinstance(result, tuple) and result[0] == STATUS_RETURN:
                return result

        return block_pc
    except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
        if e.line_number is None:
            e.line_number = current_line_number
        raise
    except Exception as e:
        raise FireflyRuntimeError(f"Error in nested for loop: {str(e)}", current_line_number)


def _execute_nested_while(lines, start_pc, variables, start_line_number=0, functions=None):
    """Execute a nested while loop within a block.

    Returns the next line index after the loop, or None on stop.

    Raises:
        FireflyRuntimeError: If execution fails
    """
    if functions is None:
        functions = {}

    line = lines[start_pc]
    stripped = line.strip()
    base_indent = get_indent(line)
    current_line_number = start_line_number + start_pc + 1

    try:
        # Parse the while loop condition
        from .parser import parse_while_block as parse_while_line
        # We need to reconstruct full lines for the parser
        temp_lines = [line]
        pc = start_pc + 1
        while pc < len(lines):
            temp_lines.append(lines[pc])
            pc += 1

        # Parse using the while block parser
        condition_str, _, _ = parse_while_line(temp_lines, 0)

        # Collect the nested block
        nested_block = []
        block_pc = start_pc + 1
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

        # Execute the loop with safety limit
        max_iterations = 100000
        iteration_count = 0

        while evaluate_expression(condition_str, variables, current_line_number):
            iteration_count += 1
            if iteration_count > max_iterations:
                raise FireflyRuntimeError(
                    f"Nested while loop exceeded maximum iterations ({max_iterations}). Possible infinite loop.",
                    current_line_number
                )

            result = _execute_block(nested_block, variables, base_indent, start_line_number + block_pc, functions)
            if result == STATUS_STOP:
                return None
            # Handle return statement
            if isinstance(result, tuple) and result[0] == STATUS_RETURN:
                return result
            if result == STATUS_REPEAT:
                continue

        return block_pc
    except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
        if e.line_number is None:
            e.line_number = current_line_number
        raise
    except Exception as e:
        raise FireflyRuntimeError(f"Error in nested while loop: {str(e)}", current_line_number)


def execute_if_block(lines, start_pc, variables, functions=None):
    """Execute an if/else-if/else chain starting at start_pc.

    Returns the next program counter after the chain, or None on stop.

    Raises:
        FireflyRuntimeError: If execution fails
        FireflySyntaxError: If the syntax is invalid
    """
    if functions is None:
        functions = {}

    pc = start_pc
    executed = False  # Track if any branch has executed

    while pc < len(lines):
        line = lines[pc].strip()
        current_line_number = pc + 1

        try:
            # Handle 'if' statement
            if line.startswith("if ") and pc == start_pc:
                _, condition, inline_action = parse_if_statement(line)
                block_lines, next_pc = _collect_block(lines, pc)

                if evaluate_expression(condition, variables, current_line_number):
                    executed = True
                    if inline_action:
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                    else:
                        for bl in block_lines:
                            status = execute_line(bl, variables, current_line_number, functions)
                            if status == STATUS_STOP:
                                return None
                pc = next_pc

            # Handle 'else if' statement
            elif line.startswith("else if "):
                # Parse as if statement (remove "else " prefix)
                _, condition, inline_action = parse_if_statement("if " + line[8:])
                block_lines, next_pc = _collect_block(lines, pc)

                if not executed and evaluate_expression(condition, variables, current_line_number):
                    executed = True
                    if inline_action:
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                    else:
                        for bl in block_lines:
                            status = execute_line(bl, variables, current_line_number, functions)
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
                        status = execute_line(inline_action, variables, current_line_number, functions)
                        if status == STATUS_STOP:
                            return None
                    else:
                        for bl in block_lines:
                            status = execute_line(bl, variables, current_line_number, functions)
                            if status == STATUS_STOP:
                                return None
                pc = next_pc

            else:
                # Not part of if/else chain, exit
                break
        except (FireflyRuntimeError, FireflySyntaxError, FireflyVariableError) as e:
            if e.line_number is None:
                e.line_number = current_line_number
            raise
        except Exception as e:
            raise FireflyRuntimeError(f"Error in if/else statement: {str(e)}", current_line_number)

    return pc
