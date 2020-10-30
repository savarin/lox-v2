import enum
from typing import Optional, Tuple

import chunk
import value

STACK_MAX = 256


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
        self.stack = None
        self.stack_top = None


def reset_stack(emulator):
    #
    """Reset VM by moving stack_top to point to beginning of array, thus
    indicating stack is empty."""
    emulator.stack = [None] * STACK_MAX
    emulator.stack_top = 0
    return emulator


def init_vm():
    # type: () -> VM
    """Initialize new VM."""
    emulator = VM()
    return reset_stack(emulator)


def free_vm(emulator):
    # type: (VM) -> None
    """Deallocates memory in VM."""
    pass


def push(emulator, val):
    # type: (VM, value.Value) -> VM
    """Push new value to the top of the stack."""
    assert emulator.stack is not None
    emulator.stack[emulator.stack_top] = val
    emulator.stack_top += 1

    return emulator


def pop(emulator):
    # type: (VM) -> Tuple[VM, value.Value]
    """Pop most recently pushed value."""
    assert emulator.stack_top is not None
    emulator.stack_top -= 1
    return emulator, emulator.stack[emulator.stack_top]


def run(emulator):
    #
    """Executes instructions in bytecode."""
    def read_byte():
        # type: () -> chunk.OpCode
        """Reads byte at current instruction pointer and advances pointer."""
        emulator.ip += 1
        return emulator.bytecode.code[emulator.ip - 1]

    def read_constant():
        # type: () -> value.Value
        """Reads next byte from bytecode, treats result as index and looks up
        corresponding location in constants table."""
        return emulator.bytecode.constants.values[read_byte()]

    while True:
        instruction = read_byte()

        if instruction == chunk.OpCode.OP_CONSTANT:
            constant = read_constant()
            emulator = push(emulator, constant)

        elif instruction == chunk.OpCode.OP_RETURN:
            emulator, constant = pop(emulator)
            print(constant)
            return InterpretResult.INTERPRET_OK


def interpret(emulator, bytecode):
    # type: (VM, chunk.Chunk) -> None
    """Implement instructions in bytecode."""
    # TODO: Compare implementation for vm.ip in 15.1.1
    emulator.bytecode = bytecode
    emulator.ip = 0

    return run(emulator)
