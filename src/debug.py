from src import chunk


def disassemble_chunk(bytecode, name):
    # type: (chunk.Chunk, str) -> None
    """Expose each instruction in chunk."""
    print("== {} ==".format(name))

    for offset in range(bytecode.count):
        offset = diassemble_instruction(bytecode, offset)


def simple_instruction(name, offset):
    # type: (str, int) -> int
    """Utility function for simple instructions."""
    print("{}".format(name))
    return offset + 1


def diassemble_instruction(bytecode, offset):
    # type: (chunk.Chunk, int) -> int
    """Expose details pertaining to each specific instruction."""
    print("{:04d}".format(offset), end=" ")

    assert bytecode.code is not None
    instruction = bytecode.code[offset]

    if instruction == chunk.OpCode.OP_RETURN:
        return simple_instruction("OP_RETURN", offset)

    print("Unknown opcode {}".format(instruction))
    return offset + 1
