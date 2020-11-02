import enum
from typing import List, Optional, Tuple

import chunk
import compiler
import scanner
import value

STACK_MAX = 8

InterpretResultTuple = Tuple["InterpretResult", Optional[value.Value], Optional[chunk.OpCode]]


class InterpretResult(enum.Enum):
    INTERPRET_OK = "INTERPRET_OK"
    INTERPRET_COMPILE_ERROR = "INTERPRET_COMPILE_ERROR"
    INTERPRET_RUNTIME_ERROR = "INTERPRET_RUNTIME_ERROR"


class VM():
    def __init__(self):
        # type: () -> None
        """Stores bytecode and current instruction pointer."""
        self.bytecode = None  # type: Optional[chunk.Chunk]
        self.ip = 0
        self.stack = None  # type: Optional[List[Optional[value.Value]]]
        self.stack_top = 0
        self.counter = 0


def reset_stack(emulator):
    # type: (VM) -> VM
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
    # type: (VM) -> VM
    """Deallocates memory in VM."""
    assert emulator.bytecode is not None
    if emulator.bytecode.code is not None:
        emulator.bytecode = chunk.free_chunk(emulator.bytecode)

    emulator.ip = 0
    return reset_stack(emulator)


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

    assert emulator.stack is not None
    val = emulator.stack[emulator.stack_top]

    assert val is not None
    return emulator, val


def peek(emulator, distance):
    # type: (VM, int) -> Tuple[VM, value.Value]
    """
    """
    assert emulator.stack is not None
    val = emulator.stack[emulator.stack_top - 1 - distance]

    assert val is not None
    return emulator, val


def read_byte(emulator):
    # type: (VM) -> Tuple[VM, chunk.Byte]
    """Reads byte at current instruction pointer and advances pointer."""
    assert emulator.ip is not None
    emulator.ip += 1

    assert emulator.bytecode is not None
    assert emulator.bytecode.code is not None
    instruction = emulator.bytecode.code[emulator.ip - 1]

    assert instruction is not None
    return emulator, instruction


def read_constant(emulator):
    # type: (VM) -> Tuple[VM, value.Value]
    """Reads next byte from bytecode, treats result as index and looks up
    corresponding location in constants table."""
    emulator, offset = read_byte(emulator)

    assert emulator.bytecode is not None
    assert emulator.bytecode.constants is not None
    assert emulator.bytecode.constants.values is not None
    assert isinstance(offset, int)
    constant = emulator.bytecode.constants.values[offset]

    assert constant is not None
    return emulator, constant


def binary_op(emulator, op):
    # type: (VM, str) -> VM
    """Execute binary operation on two items at the top of the stack."""
    while True:
        emulator, b = pop(emulator)
        emulator, a = pop(emulator)
        return push(emulator, eval("a {} b".format(op)))


def run(emulator):
    # type: (VM) -> InterpretResultTuple
    """Executes instructions in bytecode."""
    constant, opcode = None, None

    while True:
        emulator, instruction = read_byte(emulator)

        if instruction == chunk.OpCode.OP_CONSTANT:
            emulator, constant = read_constant(emulator)
            emulator = push(emulator, constant)

        elif instruction == chunk.OpCode.OP_POP:
            emulator, constant = pop(emulator)

        elif instruction == chunk.OpCode.OP_GET_LOCAL:
            emulator, slot = read_byte(emulator)
            assert emulator.stack is not None
            assert isinstance(slot, int)
            val = emulator.stack[slot]
            assert val is not None
            emulator = push(emulator, val)

        elif instruction == chunk.OpCode.OP_SET_LOCAL:
            emulator, slot = read_byte(emulator)
            assert emulator.stack is not None
            assert isinstance(slot, int)
            val = emulator.stack[slot]
            assert val is not None
            emulator, val = peek(emulator, 0)

        elif instruction == chunk.OpCode.OP_ADD:
            emulator = binary_op(emulator, "+")

        elif instruction == chunk.OpCode.OP_SUBTRACT:
            emulator = binary_op(emulator, "-")

        elif instruction == chunk.OpCode.OP_MULTIPLY:
            emulator = binary_op(emulator, "*")

        elif instruction == chunk.OpCode.OP_DIVIDE:
            emulator = binary_op(emulator, "/")

        elif instruction == chunk.OpCode.OP_NEGATE:
            emulator, constant = pop(emulator)
            constant = -constant
            emulator = push(emulator, constant)

        elif instruction == chunk.OpCode.OP_PRINT:
            emulator, constant = pop(emulator)
            assert isinstance(instruction, chunk.OpCode)
            opcode = instruction
            print(constant)

        elif instruction == chunk.OpCode.OP_RETURN:
            assert constant is not None
            return InterpretResult.INTERPRET_OK, constant, opcode


def interpret(emulator, source, debug_level):
    # type: (VM, scanner.Source, int) -> InterpretResultTuple
    """Implement instructions in bytecode."""
    # TODO: Compare implementation for vm.ip in 15.1.1
    bytecode = chunk.init_chunk()

    if not compiler.compile(source, bytecode, debug_level):
        bytecode = chunk.free_chunk(bytecode)

        return InterpretResult.INTERPRET_COMPILE_ERROR, None, None

    emulator.bytecode = bytecode
    result = run(emulator)

    bytecode = chunk.free_chunk(bytecode)
    return result
