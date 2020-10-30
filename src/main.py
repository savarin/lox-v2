import chunk
import debug
import vm


def main():
    emulator = vm.init_vm()

    bytecode = chunk.init_chunk()

    bytecode, constant = chunk.add_constant(bytecode, 1.2)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT, 123)
    bytecode = chunk.write_chunk(bytecode, constant, 123)

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN, 123)

    debug.disassemble_chunk(bytecode, "test chunk")

    vm.interpret(emulator, bytecode)
    emulator = vm.free_vm(emulator)
    bytecode = chunk.free_chunk(bytecode)


if __name__ == "__main__":
    main()
