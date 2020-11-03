


class Function():
    def __init__(self):
        # type: () -> None
        """Stores function bytecode with name and arity."""
        self.arity = 0
        self.bytecode = None
        self.name = None


def init_function():
    # type: () -> Function
    """Initialize new function."""
    function = Function()
    function.bytecode = chunk.init_chunk()

    return function


def free_function(function):
    #
    """
    """
    function.bytecode = chunk.free_chunk(function.bytecode)


def free_chunk(bytecode):
    # type: (Chunk) -> Chunk
    """Deallocates memory and calls init_chunk to leave chunk in a well-defined
    empty state."""
    assert bytecode.code is not None
    assert bytecode.lines is not None
    bytecode.code = memory.free_array(bytecode.code, bytecode.capacity)
    bytecode.lines = memory.free_array(bytecode.lines, bytecode.capacity)

    assert bytecode.constants is not None
    if bytecode.constants.values is not None:
        bytecode.constants = value.free_value_array(bytecode.constants)
        bytecode.count = 0
        bytecode.capacity = 0

    return init_chunk()



def new_function(length=8):
    #
    """
    """
    obj = allocate_object(length, ObjectType.OBJ_FUNCTION)

    return ObjectFunction(obj)    