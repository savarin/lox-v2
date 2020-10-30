from src import chunk


def test_init_chunk():
    # type: () -> None
    bytecode = chunk.init_chunk()
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    assert bytecode.count == 1
    assert bytecode.capacity == 8
    assert bytecode.code == [chunk.OpCode.OP_RETURN] + [None] * 7

    bytecode = chunk.free_chunk(bytecode)
    assert bytecode.count == 0
    assert bytecode.capacity == 0
    assert bytecode.code is None
