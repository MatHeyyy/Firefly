"""Main entry point for the Firefly interpreter"""

import sys
from firefly.interpreter import FireflyInterpreter


def main():
    interpreter = FireflyInterpreter()

    #Check if a filename was provided as an argument
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        interpreter.run_file(filename)
    else:
        # No filename provided, start REPL
        interpreter.run_repl()


if __name__ == "__main__":
    main()
