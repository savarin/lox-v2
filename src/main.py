from src import chunk
from src import debug

if __name__ == "__main__":
    bytecode = chunk.init_chunk()

    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    debug.disassemble_chunk(bytecode, "test chunk")

    bytecode = chunk.free_chunk(bytecode)
