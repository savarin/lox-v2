from enum import Enum


class OpCode(Enum):
    """Each instruction has a 1-byte operation code, which controls what kind of
    instruction we're dealing with."""
    OP_RETURN = "OP_RETURN"


class Chunk():
    def __init__(self):
        # type: () -> None
        """Stores data along with the instructions."""
        self.count = 0
        self.capacity = 0
        self.code = None


def init_chunk():
    # type: () -> Chunk
    """Initialize new chunk."""
    return Chunk()


def write_chunk(bytecode, byte):
    # type: (Chunk, int) -> Chunk
    """Append byte to the end of the chunk."""
    # If current array not have capacity for new byte, grow array.
    if bytecode.capacity < bytecode.count + 1:
        old_capacity = bytecode.capacity
        bytecode.capacity = memory.grow_capacity(old_capacity)
        bytecode.code = memory.grow_array(bytecode.code, old_capacity, bytecode.capacity)

    bytecode.code[bytecode.count] = byte
    bytecode.count += 1

    return bytecode
