# Firefly Interpreter

A custom programming language interpreter built in Python.

## Quick Start

```bash
python3 main.py yourScript.ff
```

This runs `yourScript.ff`. Omit the filename to run `myScript.ff` (a number guessing game example).

## Basic Usage

### Run a Script
```bash
python3 main.py script.ff
```

### Run in REPL Mode
```bash
python3 main.py
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

# With text styling
out styled The result is **<x>** units!
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

## Example Scripts

- `myScript.ff` - Number guessing game
- `test_comprehensive.ff` - Comprehensive language feature tests
- `test_full.ff` - Full feature test suite

