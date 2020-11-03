import chunk


def test_basic_chunk():
    # type: () -> None
    bytecode = chunk.init_chunk()
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN, 123)
    assert bytecode.count == 1
    assert bytecode.capacity == 8
    assert bytecode.code is not None
    assert bytecode.code[0] == chunk.OpCode.OP_RETURN

    bytecode = chunk.free_chunk(bytecode)
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None


def test_constant_chunk():
    # type: () -> None
    bytecode = chunk.init_chunk()

    bytecode, constant = chunk.add_constant(bytecode, 1.2)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT, 123)
    bytecode = chunk.write_chunk(bytecode, constant, 123)
    assert bytecode.count == 2
    assert bytecode.capacity == 8
    assert bytecode.code is not None
    assert bytecode.code[0] == chunk.OpCode.OP_CONSTANT
    assert bytecode.constants is not None
    assert bytecode.constants.values is not None
    assert isinstance(bytecode.code[1], int)
    assert bytecode.constants.values[bytecode.code[1]] == 1.2

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN, 123)
    assert bytecode.count == 3
    assert bytecode.capacity == 8
    assert bytecode.code is not None
    assert bytecode.code[2] == chunk.OpCode.OP_RETURN

    chunk.free_chunk(bytecode)
