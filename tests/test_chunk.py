from src import chunk


def test_init_chunk():
    # type: () -> None
    bytecode = chunk.init_chunk()
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None

    bytecode, constant = chunk.add_constant(bytecode, 1.2)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT)
    bytecode = chunk.write_chunk(bytecode, constant)
    assert bytecode.count == 2
    assert bytecode.capacity == 8
    assert bytecode.code[0] == chunk.OpCode.OP_CONSTANT
    assert bytecode.constants.values[bytecode.code[1]] == 1.2

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    assert bytecode.count == 3
    assert bytecode.capacity == 8
    assert bytecode.code[2] == chunk.OpCode.OP_RETURN

    bytecode = chunk.free_chunk(bytecode)
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None
