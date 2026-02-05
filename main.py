"""Main entry point for the Firefly interpreter"""

import sys
from firefly.interpreter import FireflyInterpreter


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else 'myScript.ff'
    """Run the Firefly interpreter"""
    interpreter = FireflyInterpreter()
    interpreter.run_file(filename)


if __name__ == "__main__":
    main()
