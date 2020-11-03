import enum

import chunk


class FunctionType(enum.Enum):
    """
    """
    TYPE_FUNCTION = "TYPE_FUNCTION"
    TYPE_SCRIPT = "TYPE_SCRIPT"


class Function():
    def __init__(self):
        # type: () -> None
        """Stores function bytecode with name and arity."""
        self.function_type = None
        self.arity = 0
        self.bytecode = None
        self.name = None


def init_function():
    # type: () -> Function
    """Initialize new function."""
    function = Function()
    function.function_type = FunctionType.TYPE_SCRIPT
    function.bytecode = chunk.init_chunk()

    return function


def free_function(function):
    #
    """
    """
    function.bytecode = chunk.free_chunk(function.bytecode)
    return init_function()
