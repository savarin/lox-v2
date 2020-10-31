import chunk

Name = str
Offset = int


def disassemble_chunk(bytecode, name):
    # type: (chunk.Chunk, Name) -> None
    """Expose each instruction in chunk."""
    print("== {} ==".format(name))
    offset = 0

    while offset < bytecode.count:
        offset = disassemble_instruction(bytecode, offset)


def constant_instruction(bytecode, name, offset):
    # type: (chunk.Chunk, Name, Offset) -> Offset
    """Utility function for constant instructions."""
    assert bytecode.code is not None
    constant = bytecode.code[offset + 1]

    assert bytecode.constants is not None
    assert bytecode.constants.values is not None
    assert isinstance(constant, int)
    val = bytecode.constants.values[constant]

    assert constant is not None
    print("{:16s} {:4d} '{}'".format(name, constant, val))
    return offset + 2


def simple_instruction(name, offset):
    # type: (Name, Offset) -> Offset
    """Utility function for simple instructions."""
    print("{}".format(name))
    return offset + 1


def disassemble_instruction(bytecode, offset):
    # type: (chunk.Chunk, Offset) -> Offset
    """Expose details pertaining to each specific instruction."""
    print("{:04d}".format(offset), end=" ")

    assert bytecode.lines is not None
    line = bytecode.lines[offset]

    assert line is not None
    if offset > 0 and line == bytecode.lines[offset - 1]:
        print("   |", end=" ")
    else:
        print("{:04d}".format(line), end=" ")

    assert bytecode.code is not None
    instruction = bytecode.code[offset]

    if instruction == chunk.OpCode.OP_CONSTANT:
        return constant_instruction(bytecode, "OP_CONSTANT", offset)
    elif instruction == chunk.OpCode.OP_ADD:
        return simple_instruction("OP_ADD", offset)
    elif instruction == chunk.OpCode.OP_SUBTRACT:
        return simple_instruction("OP_SUBTRACT", offset)
    elif instruction == chunk.OpCode.OP_MULTIPLY:
        return simple_instruction("OP_MULTIPLY", offset)
    elif instruction == chunk.OpCode.OP_DIVIDE:
        return simple_instruction("OP_DIVIDE", offset)
    elif instruction == chunk.OpCode.OP_NEGATE:
        return simple_instruction("OP_NEGATE", offset)
    elif instruction == chunk.OpCode.OP_RETURN:
        return simple_instruction("OP_RETURN", offset)

    print("Unknown opcode {}".format(instruction))
    return offset + 1
