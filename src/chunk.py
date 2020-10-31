import enum
from typing import List, Optional, Tuple, Union

import memory
import value

Byte = Union["OpCode", value.Value]
Code = Optional[List[Optional[Byte]]]
Line = int
Lines = Optional[List[Optional[Line]]]


class OpCode(enum.Enum):
    """Each instruction has a 1-byte operation code, which controls what kind of
    instruction we're dealing with."""
    OP_CONSTANT = "OP_CONSTANT"
    OP_POP = "OP_POP"
    OP_ADD = "OP_ADD"
    OP_SUBTRACT = "OP_SUBTRACT"
    OP_MULTIPLY = "OP_MULTIPLY"
    OP_DIVIDE = "OP_DIVIDE"
    OP_NEGATE = "OP_NEGATE"
    OP_PRINT = "OP_PRINT"
    OP_RETURN = "OP_RETURN"


class Chunk():
    def __init__(self):
        # type: () -> None
        """Stores data along with the instructions."""
        self.count = 0
        self.capacity = 0
        self.code = None  # type: Code
        self.lines = None  # type: Lines
        self.constants = None  # type: Optional[value.ValueArray]


def init_chunk():
    # type: () -> Chunk
    """Initialize new chunk."""
    bytecode = Chunk()
    bytecode.constants = value.init_value_array()

    return bytecode


def write_chunk(bytecode, byte, line):
    # type: (Chunk, Byte, Line) -> Chunk
    """Append byte to the end of the chunk."""
    # If current array not have capacity for new byte, grow array.
    if bytecode.capacity < bytecode.count + 1:
        old_capacity = bytecode.capacity
        bytecode.capacity = memory.grow_capacity(old_capacity)
        bytecode.code = memory.grow_array(bytecode.code, old_capacity, bytecode.capacity)
        bytecode.lines = memory.grow_array(bytecode.lines, old_capacity, bytecode.capacity)

    assert bytecode.code is not None
    assert bytecode.lines is not None
    bytecode.code[bytecode.count] = byte
    bytecode.lines[bytecode.count] = line
    bytecode.count += 1

    return bytecode


def add_constant(bytecode, val):
    # type: (Chunk, value.Value) -> Tuple[Chunk, value.Value]
    """Append value to the end of the chunk's value array."""
    assert bytecode.constants is not None
    bytecode.constants = value.write_value_array(bytecode.constants, val)
    return bytecode, bytecode.constants.count - 1


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
