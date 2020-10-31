import chunk
import vm


def test_init_vm():
    # type: () -> None
    emulator = vm.init_vm()
    bytecode = chunk.init_chunk()

    bytecode, constant = chunk.add_constant(bytecode, 1.2)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT, 123)
    bytecode = chunk.write_chunk(bytecode, constant, 123)

    bytecode, constant = chunk.add_constant(bytecode, 3.4)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT, 123)
    bytecode = chunk.write_chunk(bytecode, constant, 123)

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_ADD, 123)

    bytecode, constant = chunk.add_constant(bytecode, 4.6)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT, 123)
    bytecode = chunk.write_chunk(bytecode, constant, 123)

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_DIVIDE, 123)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_NEGATE, 123)

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN, 123)

    emulator.bytecode = bytecode
    result, constant = vm.run(emulator)
    assert result == vm.InterpretResult.INTERPRET_OK
    assert constant == -1.0

    emulator = vm.free_vm(emulator)
