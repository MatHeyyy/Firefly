"""Main interpreter for Firefly scripts"""

import os
from .executor import execute_line, execute_while_block
from .parser import STATUS_STOP


class FireflyInterpreter:
    """Interpreter for Firefly programming language"""

    def __init__(self):
        self.variables = {}

    def run_file(self, filename):
        """
        Run a Firefly script file.

        Args:
            filename: Path to the .ff script file
        """
        if not os.path.exists(filename):
            print(f"Error: '{filename}' not found.")
            return

        with open(filename, 'r') as file:
            lines = file.readlines()

        pc = 0
        while pc < len(lines):
            line = lines[pc]
            stripped = line.strip()

            # WHILE LOOP LOGIC
            if stripped.startswith("while "):
                result = execute_while_block(lines, pc, self.variables)
                if result is None:
                    return  # Stop execution
                pc = result
            else:
                status = execute_line(stripped, self.variables)
                if status == STATUS_STOP:
                    return
                pc += 1
