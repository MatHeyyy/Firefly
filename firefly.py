# FIREFLY INTERPRETER v1.0
# My first attempt at creating a programming language
# The Official Release
# @author Matei Costinescu

import sys
import os

variables = {}

def get_indent(line):
    # Convert tabs to spaces to be safe and count indentation
    line = line.expandtabs(4)
    return len(line) - len(line.lstrip())

def evaluate_expression(expr):
    # 1. Replace variables (Longest names first)
    for var in sorted(variables.keys(), key=len, reverse=True):
        if var in expr:
            val = str(variables[var])
            expr = expr.replace(var, val)
    
    # 2. Fix Logic Syntax (single = becomes == for comparison)
    if "=" in expr and "==" not in expr and "<=" not in expr and ">=" not in expr:
        expr = expr.replace("=", "==")

    try:
        return eval(expr)
    except:
        return None

def run_line(line):
    line = line.strip()
    if not line or line.startswith("#"): return "NEXT"
    if line == "stop": return "STOP"
    if line == "repeat": return "REPEAT"

    # INPUT
    if line.startswith("in "):
        if " = " in line:
            parts = line[3:].split(" = ", 1)
            var_name = parts[0].strip()
            prompt = parts[1].strip()
            val = input(prompt + " ")
            try: variables[var_name] = int(val)
            except: variables[var_name] = val
        return "NEXT"

    # MATH SHORTCUTS
    if " += " in line:
        var, val = line.split(" += ")
        return run_line(f"{var} = {var} + {val}")
    if " -= " in line:
        var, val = line.split(" -= ")
        return run_line(f"{var} = {var} - {val}")

    # ASSIGNMENT
    if " = " in line and not line.startswith("if "):
        parts = line.split(" = ", 1)
        name = parts[0].split()[-1] 
        result = evaluate_expression(parts[1].strip())
        variables[name] = result if result is not None else parts[1].strip()
        return "NEXT"

    # OUTPUT
    if line.startswith("out "):
        content = line[4:]
        for var, val in variables.items():
            content = content.replace(f"<{var}>", str(val))
        if content.startswith("**") and content.endswith("**"):
            print("\033[1m" + content.replace("**", "") + "\033[0m")
        else:
            print(content)
        return "NEXT"
    
    # IF STATEMENTS
    if line.startswith("if "):
        if " do " in line:
            parts = line[3:].split(" do ", 1)
            condition = parts[0].strip()
            action = parts[1].strip()
        else:
            condition = line[3:] 
            action = "" 

        if evaluate_expression(condition):
            return run_line(action)

    return "NEXT"

def runFile(filename):
    if not os.path.exists(filename):
        print(f"Error: '{filename}' not found.")
        return

    with open(filename, 'r') as file:
        lines = file.readlines()

    pc = 0
    while pc < len(lines):
        line = lines[pc]
        stripped = line.strip()
        
        # WHILE LOOP LOGIC
        if stripped.startswith("while "):
            # Extract Condition
            raw_content = stripped[6:]
            if raw_content.endswith(" do"):
                 condition_str = raw_content[:-3].strip()
            elif " do " in raw_content:
                 condition_str = raw_content.split(" do ")[0].strip()
            else:
                 condition_str = raw_content.strip()

            # Capture Block
            base_indent = get_indent(line)
            block_lines = []
            block_pc = pc + 1
            
            while block_pc < len(lines):
                next_line = lines[block_pc]
                if not next_line.strip(): 
                    block_pc += 1
                    continue
                
                next_indent = get_indent(next_line)
                if next_indent > base_indent:
                    block_lines.append(next_line)
                    block_pc += 1
                else:
                    break
            
            # Execute Loop
            pc = block_pc 
            loop_active = True
            
            while loop_active:
                result = evaluate_expression(condition_str)
                if not result:
                    loop_active = False
                    break

                for bl in block_lines:
                    status = run_line(bl)
                    if status == "STOP":
                        loop_active = False
                        break
                    if status == "REPEAT":
                        break 
        else:
            run_line(stripped)
            pc += 1

# Start the Engine
runFile('myScript.ff')