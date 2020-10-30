from src import chunk

if __name__ == "__main__":
    bytecode = chunk.init_chunk()
    bytecode = chunk.write_chunk(bytecode, chunk.OpCode.OP_RETURN)
    bytecode = chunk.free_chunk(bytecode)
