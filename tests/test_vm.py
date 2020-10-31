import chunk
import vm


def test_manual_init():
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
    result = vm.run(emulator)
    assert result[0] == vm.InterpretResult.INTERPRET_OK
    assert result[1] == -1.0
    assert result[2] is None

    emulator = vm.free_vm(emulator)


def interpret(source, result, constant, opcode):
    #
    emulator = vm.init_vm()
    result_tuple = vm.interpret(emulator, source, 0)

    assert result_tuple[0] == result
    assert result_tuple[1] == constant
    assert result_tuple[2] == opcode

    emulator = vm.free_vm(emulator)


def test_basic_add():
    # type: () -> None
    interpret(
        source="1 + 1;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=2,
        opcode=None,
    )


def test_basic_subtract():
    # type: () -> None
    interpret(
        source="2 - 1;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=1,
        opcode=None,
    )


def test_basic_multiply():
    # type: () -> None
    interpret(
        source="3 * 3;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=9,
        opcode=None,
    )


def test_basic_divide():
    # type: () -> None
    interpret(
        source="9 / 3;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=3,
        opcode=None,
    )


def test_basic_negate():
    # type: () -> None
    interpret(
        source="-1;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=-1,
        opcode=None,
    )


def test_basic_print():
    # type: () -> None
    interpret(
        source="print 1;",
        result=vm.InterpretResult.INTERPRET_OK,
        constant=1,
        opcode=chunk.OpCode.OP_PRINT,
    )
