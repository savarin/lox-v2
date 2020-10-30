import chunk
import debug


def main1():
    bytecode = chunk.init_chunk()

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    debug.disassemble_chunk(bytecode, "test chunk")

    bytecode = chunk.free_chunk(bytecode)


def main2():
    bytecode = chunk.init_chunk()

    bytecode, constant = chunk.add_constant(bytecode, 1.2)
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_CONSTANT)
    bytecode = chunk.write_chunk(bytecode, constant)

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    debug.disassemble_chunk(bytecode, "test chunk")
    bytecode = chunk.free_chunk(bytecode)


if __name__ == "__main__":
    main2()
