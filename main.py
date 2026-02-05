"""Main entry point for the Firefly interpreter"""

import sys
from firefly.interpreter import FireflyInterpreter
from firefly.errors import FireflyError


def main():
    """Main entry point with error handling"""
    try:
        interpreter = FireflyInterpreter()

        # Check if a filename was provided as an argument
        if len(sys.argv) > 1:
            filename = sys.argv[1]
            interpreter.run_file(filename)
        else:
            # No filename provided, start REPL
            interpreter.run_repl()
    except FireflyError:
        # Error already printed by the interpreter
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
