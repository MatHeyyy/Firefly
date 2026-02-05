"""Main interpreter for Firefly scripts"""

import os
import sys
from .executor import execute_line, execute_while_block, execute_for_block, execute_if_block
from .parser import STATUS_STOP
from .errors import (
    FireflyError, FireflySyntaxError, FireflyRuntimeError,
    FireflyVariableError, FireflyFileError
)


class FireflyInterpreter:
    """Interpreter for Firefly programming language"""

    def __init__(self):
        self.variables = {}

    def run_file(self, filename):
        """
        Run a Firefly script file.

        Args:
            filename: Path to the .ff script file

        Raises:
            FireflyFileError: If the file cannot be read
            FireflyError: If execution fails
        """
        if not os.path.exists(filename):
            error_msg = f"File '{filename}' not found."
            print(f"Error: {error_msg}", file=sys.stderr)
            raise FireflyFileError(error_msg)

        try:
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except PermissionError:
            error_msg = f"Permission denied: Cannot read '{filename}'"
            print(f"Error: {error_msg}", file=sys.stderr)
            raise FireflyFileError(error_msg)
        except UnicodeDecodeError:
            error_msg = f"File '{filename}' contains invalid characters"
            print(f"Error: {error_msg}", file=sys.stderr)
            raise FireflyFileError(error_msg)
        except Exception as e:
            error_msg = f"Error reading file '{filename}': {str(e)}"
            print(f"Error: {error_msg}", file=sys.stderr)
            raise FireflyFileError(error_msg)

        if not lines:
            print(f"Warning: File '{filename}' is empty", file=sys.stderr)
            return

        pc = 0
        try:
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
                    status = execute_line(stripped, self.variables, pc + 1)
                    if status == STATUS_STOP:
                        return
                    pc += 1
        except FireflyError as e:
            # FireflyError already has formatted message with line number
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user.", file=sys.stderr)
            sys.exit(130)
        except Exception as e:
            print(f"Unexpected error at line {pc + 1}: {str(e)}", file=sys.stderr)
            sys.exit(1)

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
            except EOFError:
                # Handle Ctrl+D gracefully
                print("\nExiting Firefly REPL. Goodbye!")
                break
            except FireflyError as e:
                # Handle Firefly-specific errors
                print(f"Error: {e}", file=sys.stderr)
            except Exception as e:
                # Catch and display any other errors
                print(f"Unexpected error: {e}", file=sys.stderr)
