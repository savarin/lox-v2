import chunk


def disassemble_chunk(bytecode, name):
    # type: (chunk.Chunk, str) -> None
    """Expose each instruction in chunk."""
    print("\n== {} ==".format(name))
    offset = 0

    while offset < bytecode.count:
        offset = disassemble_instruction(bytecode, offset)

    print("")


def constant_instruction(opcode_name, offset, bytecode):
    # type: (str, int, chunk.Chunk) -> int
    """Utility function for constant instructions."""
    assert bytecode.code is not None
    constant = bytecode.code[offset + 1]

    assert bytecode.constants is not None
    assert bytecode.constants.values is not None
    assert isinstance(constant, int)
    val = bytecode.constants.values[constant]

    assert constant is not None
    print("{:16s} {:4d} '{}'".format(opcode_name, constant, val))
    return offset + 2


def simple_instruction(opcode_name, offset):
    # type: (str, int) -> int
    """Utility function for simple instructions."""
    print("{}".format(opcode_name))
    return offset + 1


def byte_instruction(opcode_name, offset, bytecode):
    #
    """
    """
    slot = bytecode.code[offset + 1]

    print("{:16s} {:4d}".format(opcode_name, slot))
    return offset + 2


def disassemble_instruction(bytecode, offset):
    # type: (chunk.Chunk, int) -> int
    """Expose details pertaining to each specific instruction."""
    print("{:04d}".format(offset), end=" ")

    assert bytecode.lines is not None
    line = bytecode.lines[offset]

    assert line is not None
    if offset > 0 and line == bytecode.lines[offset - 1]:
        print("   |", end=" ")
    else:
        print("{:4d}".format(line), end=" ")

    assert bytecode.code is not None
    instruction = bytecode.code[offset]

    if instruction == chunk.OpCode.OP_CONSTANT:
        return constant_instruction("OP_CONSTANT", offset, bytecode)
    elif instruction == chunk.OpCode.OP_POP:
        return simple_instruction("OP_POP", offset)
    elif instruction == chunk.OpCode.OP_GET_LOCAL:
        return byte_instruction("OP_GET_LOCAL", offset, bytecode)
    elif instruction == chunk.OpCode.OP_SET_LOCAL:
        return byte_instruction("OP_SET_LOCAL", offset, bytecode)
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
    elif instruction == chunk.OpCode.OP_PRINT:
        return simple_instruction("OP_PRINT", offset)
    elif instruction == chunk.OpCode.OP_RETURN:
        return simple_instruction("OP_RETURN", offset)

    print("Unknown opcode {}".format(instruction))
    return offset + 1
