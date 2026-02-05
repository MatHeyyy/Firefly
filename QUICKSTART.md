# Quick Start Guide - Firefly Interpreter

## Running Your Scripts

### Option 1: Run a Custom Script
```bash
python3 main.py myScript.ff
```
This runs `myScript.ff`. Make sure the file exists in the same directory or provide the full path.

### Option 2: Interactive REPL Mode
```bash
python3 main.py
```
You can also use REPL mode to run Firefly commands interactively.

```plain
Firefly v1.0 Interactive Mode
Type 'exit' to quit.
------------------------------
firefly>> num x = 10
firefly>> x += 5
firefly>> out <x>
15
```

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

# Text styling (use "out styled" to enable styling)
out This **will not** be //styled//              # Plain output shows markers as-is
out styled This **will** be //styled//           # Bold and italic applied
out styled **Bold** and //italic// and normal    # Mix styles in one line
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
# While loop example
while attempts > 0 do
    out Attempts left: <attempts>
    in guess = Guess:
    attempts -= 1
    
# For loop example
for i in 1 to 5 do
    out Number: <i>
```

### Comments
```firefly
# This is a comment
num x = 5  # Inline comment
```

## Example Script

Save this as `example.ff`:
```firefly
out styled **Welcome to the Number Game!**

num secret = 7
num attempts = 3

while attempts > 0 do
    out You have <attempts> attempts left.
    in guess = Guess the number (1-10):
    
    if guess = secret do out styled **Correct! You win!**
    if guess = secret do stop
    
    if guess > secret do out styled Too //high//!
    if guess < secret do out styled Too //low//!
    
    attempts -= 1
    if attempts = 0 do out Sorry, game over. The number was <secret>.

out Thanks for playing!
```

Then run it:
```bash
python3 main.py example.ff
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

main.py                 # Entry point - accepts script filename as argument
myScript.ff             # Sample guessing game
example.ff              # Your custom scripts
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
