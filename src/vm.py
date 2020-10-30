import enum
from typing import Optional

import chunk


class InterpretResult(enum.Enum):
    INTERPRET_OK = "INTERPRET_OK"
    INTERPRET_COMPILE_ERROR = "INTERPRET_COMPILE_ERROR"
    INTERPRET_RUNTIME_ERROR = "INTERPRET_RUNTIME_ERROR"


class VM():
    def __init__(self):
        # type: () -> None
        """Stores bytecode and current instruction pointer."""
        self.bytecode = None  # type: Optional[chunk.Chunk]
        self.ip = None  # type: Optional[int]


def init_vm():
    # type: () -> VM
    """Initialize new VM."""
    return VM()


def free_vm(emulator):
    # type: (VM) -> None
    """Deallocates memory in VM."""
    pass


def run(emulator):
    #
    """Executes instructions in bytecode."""
    def read_byte():
        # type: () -> chunk.OpCode
        """Reads byte at current instruction pointer and advances pointer."""
        emulator.ip += 1
        return emulator.bytecode.code[emulator.ip - 1]

    def read_constant():
        # type: () -> int
        """Reads next byte from bytecode, treats result as index and looks up
        corresponding location in constants table."""
        return emulator.bytecode.constants.values[read_byte()]

    while True:
        instruction = read_byte()

        if instruction == chunk.OpCode.OP_CONSTANT:
            constant = read_constant()
            print(constant)
            break

        elif instruction == chunk.OpCode.OP_RETURN:
            return InterpretResult.INTERPRET_OK


def interpret(emulator, bytecode):
    # type: (VM, chunk.Chunk) -> None
    """Implement instructions in bytecode."""
    # TODO: Compare implementation for vm.ip in 15.1.1
    emulator.bytecode = bytecode
    emulator.ip = 0

    return run(emulator)
