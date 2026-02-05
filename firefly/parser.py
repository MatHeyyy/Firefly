"""Parser for Firefly script syntax"""

from .utils import get_indent
from .errors import FireflySyntaxError, FireflyIndentationError


# Status constants
STATUS_NEXT = "NEXT"
STATUS_STOP = "STOP"
STATUS_REPEAT = "REPEAT"


def parse_input_statement(line):
    """Parse an input statement (in var = prompt)"""
    if " = " not in line:
        raise FireflySyntaxError(f"Invalid input statement syntax: '{line}'. Expected 'in var = prompt'")

    parts = line[3:].split(" = ", 1)
    if len(parts) != 2:
        raise FireflySyntaxError(f"Invalid input statement syntax: '{line}'. Expected 'in var = prompt'")

    var_name = parts[0].strip()
    prompt = parts[1].strip()

    if not var_name:
        raise FireflySyntaxError(f"Variable name cannot be empty in input statement: '{line}'")

    return ("input", var_name, prompt)


def parse_math_shortcut(line):
    """Parse math shortcuts (+= and -=)"""
    # Don't match if line starts with keywords that might contain += or -=
    if line.startswith("out ") or line.startswith("if ") or line.startswith("in "):
        return None

    if " += " in line:
        var, val = line.split(" += ", 1)
        return ("math_shortcut", var.strip(), "+", val.strip())
    elif " -= " in line:
        var, val = line.split(" -= ", 1)
        return ("math_shortcut", var.strip(), "-", val.strip())
    return None


def parse_assignment(line):
    """Parse variable assignment (with optional type prefix like 'num')"""
    if " = " in line and not line.startswith("if "):
        parts = line.split(" = ", 1)
        name = parts[0].strip()
        value = parts[1].strip()

        # Remove type prefixes like 'num', 'str', etc. (e.g., "num x" -> "x")
        if " " in name:
            tokens = name.split()
            if len(tokens) >= 2:
                name = tokens[-1]

        return ("assignment", name, value)
    return None


def parse_output_statement(line):
    """Parse an output statement (out ... or out styled ...)"""
    if line.startswith("out styled "):
        content = line[11:]  # Skip "out styled "
        return ("output", content, True)  # True indicates styling should be applied
    else:
        content = line[4:]  # Skip "out "
        return ("output", content, False)  # False indicates no styling


def parse_if_statement(line):
    """Parse an if statement"""
    # Handle "if condition do action" (inline action)
    if " do " in line:
        parts = line[3:].split(" do ", 1)
        condition = parts[0].strip()
        action = parts[1].strip()
    # Handle "if condition do" (block-style, no inline action)
    elif line.endswith(" do"):
        condition = line[3:-3].strip()
        action = ""
    else:
        condition = line[3:].strip()
        action = ""
    return ("if", condition, action)

def parse_else_statement(line):
    """
    Parse an else statement while keeping it dynamic
    for example "else do", "else if", "else for", "else while" or just "else"
    """
    stripped = line.strip()
    if stripped.startswith("else "):
        return stripped[5:].strip()  # Return the part after "else "
    elif stripped == "else":
        return ""  # Just "else" with no additional keywords
    else:
        return None  # Not an else statement


def parse_while_block(lines, start_pc):
    """
    Parse a while loop block and return the condition and block lines.

    Returns:
        (condition, block_lines, next_pc)
    """
    line = lines[start_pc]
    stripped = line.strip()

    # Extract Condition
    raw_content = stripped[6:]
    if raw_content.endswith(" do"):
        condition_str = raw_content[:-3].strip()
    elif " do " in raw_content:
        condition_str = raw_content.split(" do ")[0].strip()
    else:
        condition_str = raw_content.strip()

    # Capture Block
    base_indent = get_indent(line)
    block_lines = []
    block_pc = start_pc + 1

    while block_pc < len(lines):
        next_line = lines[block_pc]
        if not next_line.strip():
            block_pc += 1
            continue

        next_indent = get_indent(next_line)
        if next_indent > base_indent:
            block_lines.append(next_line)
            block_pc += 1
        else:
            break

    return condition_str, block_lines, block_pc

def parse_for_block(lines, start_pc):
    """
    Parse a for loop block and return the loop variable, iterable, block lines, and next PC.
    example line: for i in 0 to 5 do

    Returns:
        (loop_var, iterable, block_lines, next_pc)

    Raises:
        FireflySyntaxError: If the for loop syntax is invalid
        FireflyIndentationError: If the block is not properly indented
    """
    line = lines[start_pc]
    stripped = line.strip()

    # Extract Loop Variable and Iterable
    raw_content = stripped[4:]
    if raw_content.endswith(" do"):
        raw_content = raw_content[:-3].strip()

    if " in " not in raw_content:
        raise FireflySyntaxError(f"Invalid for loop syntax: '{stripped}'. Expected 'for var in iterable do'")

    loop_var, iterable = raw_content.split(" in ", 1)
    loop_var = loop_var.strip()
    iterable = iterable.strip()

    if not loop_var:
        raise FireflySyntaxError(f"Loop variable cannot be empty in for loop: '{stripped}'")
    if not iterable:
        raise FireflySyntaxError(f"Iterable cannot be empty in for loop: '{stripped}'")

    # Convert "0 to 10" syntax to range(0, 11)
    if " to " in iterable:
        parts = iterable.split(" to ")
        if len(parts) == 2:
            start = parts[0].strip()
            end = parts[1].strip()
            iterable = f"range({start}, {end} + 1)"
        else:
            raise FireflySyntaxError(f"Invalid 'to' syntax in for loop: '{stripped}'")

    # Capture Block
    base_indent = get_indent(line)
    block_lines = []
    block_pc = start_pc + 1

    while block_pc < len(lines):
        next_line = lines[block_pc]
        if not next_line.strip():
            block_pc += 1
            continue

        next_indent = get_indent(next_line)
        if next_indent > base_indent:
            block_lines.append(next_line)
            block_pc += 1
        else:
            break

    if not block_lines:
        raise FireflyIndentationError(f"For loop at line {start_pc + 1} has no indented block")

    return loop_var, iterable, block_lines, block_pc

def parse_function_definition(line):
        """
        Parses: function greet contains first-name and last-name do
        Returns: (func_name, arg_names)
        """
        # Remove "function " prefix
        raw_content = line[9:].strip()

        # Remove trailing " do" if present
        if raw_content.endswith(" do"):
            raw_content = raw_content[:-3].strip()

        # Check if there are arguments
        if " contains " in raw_content:
            name_part, args_part = raw_content.split(" contains ", 1)
            func_name = name_part.strip()
            # Split arguments by " and "
            arg_names = [arg.strip() for arg in args_part.split(" and ")]
        else:
            # No arguments, just function name
            func_name = raw_content.strip()
            arg_names = []

        return func_name, arg_names

def parse_function_call(line):
    """
        Parses: greet with Matei and Costinescu
        Returns: (func_name, arg_values)
        """
    if " with " in line:
        func_name, args_part = line.split(" with ")
        # split arguments by " and "
        arg_values = [val.strip() for val in args_part.split(" and ")]
        return func_name.strip(), arg_values

    # No arguments, just function name
    return line.strip(), []
