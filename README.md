# Firefly Interpreter

A custom programming language interpreter built in Python.

## Quick Start

```bash
python3 main.py
```

This runs `myScript.ff` - a number guessing game example.

## Basic Usage

### Run a Script
Edit `main.py` and change the filename to run your script:
```bash
python3 main.py yourScript.ff
```

### Use as a Library
```python
from firefly.interpreter import FireflyInterpreter

interpreter = FireflyInterpreter()
interpreter.run_file('script.ff')
```

## Language Syntax

See [QUICKSTART.md](QUICKSTART.md) for complete syntax reference.

### Quick Example
```firefly
num x = 10
x += 5
out The result is <x>
```

## Project Structure

```
firefly/              # Main package
├── interpreter.py   # Main interpreter class
├── executor.py      # Statement execution
├── parser.py        # Syntax parsing
├── evaluator.py     # Expression evaluation
└── utils.py         # Helper functions

main.py              # Entry point
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Language syntax and examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Code structure and adding features

## Files

- `myScript.ff` - Example guessing game script

