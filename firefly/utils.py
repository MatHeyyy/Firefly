"""Utility functions for the Firefly interpreter"""


def get_indent(line):
    """Convert tabs to spaces and count indentation level"""
    line = line.expandtabs(4)
    return len(line) - len(line.lstrip())
