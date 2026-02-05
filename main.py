"""Main entry point for the Firefly interpreter"""

from firefly.interpreter import FireflyInterpreter


def main():
    """Run the Firefly interpreter"""
    interpreter = FireflyInterpreter()
    interpreter.run_file('myScript.ff')


if __name__ == "__main__":
    main()
