# Architecture & Adding Features

## Code Structure

### Execution Flow
```
Your Script (.ff file)
    ↓
interpreter.py reads lines
    ↓
parser.py identifies statement type
    ↓
executor.py executes it
    ├→ evaluator.py evaluates expressions
    └→ variables dictionary updated
    ↓
Repeat until done
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `interpreter.py` | Reads .ff files, loops through lines, orchestrates execution |
| `parser.py` | Identifies statement types (input, output, assignment, if, while, etc.) |
| `executor.py` | Executes statements, handles control flow |
| `evaluator.py` | Evaluates math expressions and conditions |
| `utils.py` | Helper functions (indentation, etc.) |

## Adding New Features Safely

### Step 1: Add Parser (parser.py)

Create a function to parse your new statement type:

```python
def parse_your_feature(line):
    """Parse your feature statement"""
    # Extract data from line
    # Return tuple: (statement_type, data...)
    return ("your_feature", extracted_data)
```

### Step 2: Add Executor (executor.py)

Add execution logic in `execute_line()` function:

```python
# In execute_line() function, add:
if line.startswith("your_feature "):
    parsed = parse_your_feature(line)
    # Handle the feature
    return STATUS_NEXT
```

### Step 3: Test It

Create a test script and verify it works:

```python
from firefly.interpreter import FireflyInterpreter

interpreter = FireflyInterpreter()
interpreter.run_file('test_your_feature.ff')
```

## Example: Adding a "repeat N times" Loop

### Step 1: Parse
```python
# In parser.py
def parse_repeat_statement(line):
    """Parse: repeat 5 do"""
    if " do" in line:
        count_str = line[7:].split(" do")[0].strip()  # Extract count
        return ("repeat", count_str)
    return None
```

### Step 2: Execute
```python
# In executor.py, in execute_line():
if line.startswith("repeat "):
    parsed = parse_repeat_statement(line)
    if parsed:
        _, count_str = parsed
        count = evaluate_expression(count_str, variables)
        # Run block N times
        return STATUS_NEXT
```

### Step 3: Test
```firefly
repeat 3 do
    out Hello!
```

## Tips for Safe Changes

✅ **Do:**
- Keep parsing separate from execution
- Test in isolation before running full scripts
- Return consistent tuple format from parsers
- Use existing evaluator for expressions

❌ **Don't:**
- Modify global variables directly
- Change parser output format without updating executor
- Skip testing your changes
- Add complex logic to parser (keep it simple)

## How Features Work

### 1. Variables
Stored in a dictionary that gets passed around:
```python
variables = {'x': 10, 'y': 20}
```

### 2. Parsing
Every statement gets parsed to identify what it is:
```python
("assignment", "x", "5")
("output", "Hello <x>")
("if", "x > 5", "out True")
```

### 3. Execution
Each statement type has its own execution logic. The executor:
- Substitutes variables
- Evaluates expressions
- Updates variables
- Controls flow (loops, conditionals)

## Status Codes

Functions return these to control flow:
- `STATUS_NEXT` - Continue to next line
- `STATUS_STOP` - Stop execution
- `STATUS_REPEAT` - Continue loop

## Testing Your Changes

```python
# Test parser
from firefly.parser import parse_your_feature
result = parse_your_feature("your_feature something")
assert result[0] == "your_feature"

# Test executor
from firefly.executor import execute_line
variables = {}
status = execute_line("your_feature data", variables)
assert status == STATUS_NEXT

# Test full script
from firefly.interpreter import FireflyInterpreter
interpreter = FireflyInterpreter()
interpreter.run_file('test.ff')
```

## Common Changes

### Add a New Keyword
1. Add to `parser.py` - create parse function
2. Add to `executor.py` - add to `execute_line()`
3. Test with a `.ff` script

### Add an Operator
1. Add to `evaluator.py` - extend the eval() expression
2. Test with a script using the operator

### Add a Built-in Function
1. Add to `executor.py` - create execution logic
2. Add to `evaluator.py` - if it's an expression function

## Architecture Benefits

✅ Each module has one job  
✅ Easy to test individual parts  
✅ Changes are isolated  
✅ New features don't break old ones  
✅ Clear flow from parsing → execution  

## That's It!

The modular design makes adding features straightforward and safe. Follow the pattern: Parse → Execute → Test.
