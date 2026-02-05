"""Custom exceptions for the Firefly interpreter"""


class FireflyError(Exception):
    """Base exception for all Firefly errors"""
    def __init__(self, message, line_number=None):
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


class FireflySyntaxError(FireflyError):
    """Raised when there's a syntax error in Firefly code"""
    pass


class FireflyRuntimeError(FireflyError):
    """Raised when there's a runtime error during execution"""
    pass


class FireflyVariableError(FireflyError):
    """Raised when there's an undefined variable or variable error"""
    pass


class FireflyTypeError(FireflyError):
    """Raised when there's a type mismatch or invalid type operation"""
    pass


class FireflyFileError(FireflyError):
    """Raised when there's a file-related error"""
    pass


class FireflyIndentationError(FireflyError):
    """Raised when there's an indentation error"""
    pass
