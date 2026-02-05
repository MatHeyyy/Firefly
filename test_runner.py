#!/usr/bin/env python3
"""Test the refactored interpreter with a custom script"""

from firefly.interpreter import FireflyInterpreter

interpreter = FireflyInterpreter()
interpreter.run_file('test_full.ff')
