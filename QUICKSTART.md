# Quick Start Guide - Firefly Interpreter

## Running Your Scripts

### Option 1: Run the Default Script
```bash
python3 main.py
```
This runs `myScript.ff` - the guessing game.

### Option 2: Run a Custom Script
```bash
python3 main.py otherScript.ff
```
This runs `otherScript.ff` instead. Make sure the file exists in the same directory or provide the full path.

### Option 3: Use Programmatically
```python
from firefly.interpreter import FireflyInterpreter

interpreter = FireflyInterpreter()
interpreter.run_file('myScript.ff')
print(interpreter.variables)  # Access variables after execution
```

## Firefly Language Cheat Sheet

### Variables
```firefly
num count = 10          # Number variable
str name = Alice        # String variable (type prefix is optional)
x = 42                  # Works without type prefix too
```

### Input & Output
```firefly
in name = What is your name?
out Hello <name>!
out **Bold message**    # Text between ** is bold
```

### Math Operations
```firefly
num sum = 10 + 5
num diff = 20 - 3
num product = 4 * 5
num quotient = 20 / 4
```

### Math Shortcuts
```firefly
counter += 1            # counter = counter + 1
health -= 5             # health = health - 5
```

### Comparisons
```firefly
if x = 5 do out Equal
if x > 5 do out Greater
if x < 5 do out Less
if x >= 5 do out Greater or Equal
if x <= 5 do out Less or Equal
```

### Conditionals
```firefly
if guess = secret do out **YOU WIN!**
if attempts = 0 do stop
```

### Loops
```firefly
while attempts > 0 do
    out Attempts left: <attempts>
    in guess = Guess:
    attempts -= 1
```

### Comments
```firefly
# This is a comment
num x = 5  # Inline comment
```

## Example Script

Save this as `example.ff`:
```firefly
out **Welcome to the Number Game!**

num secret = 7
num attempts = 3

while attempts > 0 do
    out You have <attempts> attempts left.
    in guess = Guess the number (1-10):
    
    if guess = secret do out **Correct! You win!**
    if guess = secret do stop
    
    if guess > secret do out Too high!
    if guess < secret do out Too low!
    
    attempts -= 1
    if attempts = 0 do out Sorry, game over. The number was <secret>.

out Thanks for playing!
```

Then run it:
```bash
# Edit main.py to use 'example.ff' instead of 'myScript.ff'
python3 main.py
```

## Project Structure

```
firefly/                 # Package directory
├── __init__.py         # Package initialization
├── utils.py            # Helper functions
├── evaluator.py        # Expression evaluation
├── parser.py           # Parses statements
├── executor.py         # Executes statements
└── interpreter.py      # Main interpreter class

main.py                 # Entry point - EDIT THIS TO RUN DIFFERENT SCRIPTS
myScript.ff             # Sample guessing game
```

## Troubleshooting

### Script not found
Make sure your `.ff` file is in the same directory as `main.py`, or use the full path:
```python
interpreter.run_file('/full/path/to/script.ff')
```

### Variable not working
Remember to use the `<variable_name>` syntax when referencing variables in output:
```firefly
num x = 42
out The value is <x>     # Correct
out The value is x       # Wrong - prints literal 'x'
```

### Loop not working
Make sure your block is indented with spaces:
```firefly
while x > 0 do
    out x              # This line must be indented
    x -= 1
```

### Comparison not working
Single `=` is automatically converted to `==` for comparisons:
```firefly
if x = 5 do out Equal   # The parser converts = to ==
```

Happy coding! 
