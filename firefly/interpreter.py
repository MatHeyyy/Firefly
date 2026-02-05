"""Main interpreter for Firefly scripts"""

import os
from .executor import execute_line, execute_while_block, execute_for_block, execute_if_block
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

            # IF / ELSE CHAINS
            if stripped.startswith("if "):
                result = execute_if_block(lines, pc, self.variables)
                if result is None:
                    return
                pc = result
            # WHILE LOOP LOGIC
            elif stripped.startswith("while "):
                result = execute_while_block(lines, pc, self.variables)
                if result is None:
                    return  # Stop execution
                pc = result
            # FOR LOOP LOGIC
            elif stripped.startswith("for "):
                result = execute_for_block(lines, pc, self.variables)
                if result is None:
                    return  # Stop execution
                pc = result
            else:
                status = execute_line(stripped, self.variables)
                if status == STATUS_STOP:
                    return
                pc += 1

    def run_repl(self):
        """Start an interactive REPL session for Firefly"""
        print("Firefly v1.0 Interactive Mode")
        print("Type 'exit' to quit.")
        print("-" * 30)

        while True:
            try:
                # Get input with a custom prompt
                code = input("firefly>> ")

                # Handle the exit command
                if code.strip().lower() == "exit":
                    print("Exiting Firefly REPL. Goodbye!")
                    break

                # Execute the single line
                status = execute_line(code, self.variables)

                # Handle the stop command
                if status == STATUS_STOP:
                    print("Execution stopped.")
                    break

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\nType 'exit' to quit.")
            except Exception as e:
                # Catch and display any errors
                print(f"Error: {e}")
