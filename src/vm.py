import enum
from typing import List, Optional, Tuple

import chunk
import compiler
import scanner
import value

FRAMES_MAX = 8
STACK_MAX = 8

InterpretResultTuple = Tuple["InterpretResult", Optional[chunk.OpCode], Optional[List[value.Value]]]


class InterpretResult(enum.Enum):
    INTERPRET_OK = "INTERPRET_OK"
    INTERPRET_COMPILE_ERROR = "INTERPRET_COMPILE_ERROR"
    INTERPRET_RUNTIME_ERROR = "INTERPRET_RUNTIME_ERROR"


class CallFrame():
    def __init__(self, fun, ip, slots):
        #
        """
        """
        self.fun = fun
        self.ip = ip
        self.slots = slots


class VM():
    def __init__(self):
        # type: () -> None
        """Stores bytecode and current instruction pointer."""
        self.frames = None
        self.frame_count = 0
        # self.bytecode = None  # type: Optional[chunk.Chunk]
        # self.ip = 0
        self.stack = None  # type: Optional[List[Optional[value.Value]]]
        self.stack_top = 0
        self.counter = 0
        self.output = None  # type: Optional[List[value.Value]]


def reset_stack(emulator):
    # type: (VM) -> VM
    """Reset VM by moving stack_top to point to beginning of array, thus
    indicating stack is empty."""
    emulator.frames = [CallFrame(None, 0, None) for _ in range(FRAMES_MAX)]
    emulator.stack = [None] * STACK_MAX
    emulator.stack_top = 0
    emulator.output = []

    return emulator


def init_vm():
    # type: () -> VM
    """Initialize new VM."""
    emulator = VM()

    return reset_stack(emulator)


def free_vm(emulator):
    # type: (VM) -> VM
    """Deallocates memory in VM."""
    for i in range(emulator.frame_count):
        frame = emulator.frames[i]
        bytecode = frame.fun.bytecode

        if bytecode.code is not None:
            bytecode = chunk.free_chunk(bytecode)

    # assert emulator.bytecode is not None
    # if emulator.bytecode.code is not None:
    #     emulator.bytecode = chunk.free_chunk(emulator.bytecode)

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
    emulator.stack_top -= 1

    assert emulator.stack is not None
    val = emulator.stack[emulator.stack_top]

    assert val is not None
    return emulator, val


def peek(emulator, distance):
    # type: (VM, int) -> Tuple[VM, value.Value]
    """Reads value but does not pop it."""
    assert emulator.stack is not None
    val = emulator.stack[emulator.stack_top - 1 - distance]

    assert val is not None
    return emulator, val


def read_byte(frame):
    # type: (VM) -> Tuple[VM, chunk.Byte]
    """Reads byte at current instruction pointer and advances pointer."""
    frame.ip += 1
    instruction = frame.fun.bytecode.code[frame.ip - 1]
    return frame, instruction

    # emulator.ip += 1

    # assert emulator.bytecode is not None
    # assert emulator.bytecode.code is not None
    # instruction = emulator.bytecode.code[emulator.ip - 1]

    # assert instruction is not None
    # return emulator, instruction


def read_constant(frame):
    # type: (VM) -> Tuple[VM, value.Value]
    """Reads next byte from bytecode, treats result as index and looks up
    corresponding location in constants table."""
    frame, offset = read_byte(frame)
    constant = frame.fun.bytecode.constants.values[offset]
    return frame, constant


    # emulator, offset = read_byte(emulator)

    # assert emulator.bytecode is not None
    # assert emulator.bytecode.constants is not None
    # assert emulator.bytecode.constants.values is not None
    # assert isinstance(offset, int)
    # constant = emulator.bytecode.constants.values[offset]

    # assert constant is not None
    # return emulator, constant


def binary_op(emulator, op):
    # type: (VM, str) -> VM
    """Execute binary operation on two items at the top of the stack."""
    emulator, b = pop(emulator)
    emulator, a = pop(emulator)

    return push(emulator, eval("a {} b".format(op)))


def run(emulator):
    # type: (VM) -> InterpretResultTuple
    """Executes instructions in bytecode."""
    frame = emulator.frames[emulator.frame_count - 1]

    while True:
        frame, instruction = read_byte(frame)

        if instruction == chunk.OpCode.OP_CONSTANT:
            frame, constant = read_constant(frame)
            emulator = push(emulator, constant)

            # emulator, constant = read_constant(emulator)
            # emulator = push(emulator, constant)

        elif instruction == chunk.OpCode.OP_POP:
            emulator, constant = pop(emulator)

        elif instruction == chunk.OpCode.OP_GET_LOCAL:
            frame, slot = read_byte(frame)
            val = frame.slots[slot]
            if val is None:
                break
            emulator = push(emulator, val)

            # emulator, slot = read_byte(emulator)
            # assert isinstance(slot, int)
            # assert emulator.stack is not None
            # val = emulator.stack[slot]
            # if val is None:
            #     break
            # emulator = push(emulator, val)

        elif instruction == chunk.OpCode.OP_SET_LOCAL:
            frame, slot = read_byte(frame)
            emulator, val = peek(emulator, 0)
            frame.slots[slot] = val

            # emulator, slot = read_byte(emulator)
            # emulator, val = peek(emulator, 0)
            # assert isinstance(slot, int)
            # assert emulator.stack is not None
            # emulator.stack[slot] = val

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
            print(constant)
            assert emulator.output is not None
            emulator.output.append(constant)

        elif instruction == chunk.OpCode.OP_RETURN:
            assert isinstance(instruction, chunk.OpCode)
            return InterpretResult.INTERPRET_OK, instruction, emulator.output

    assert isinstance(instruction, chunk.OpCode)
    return InterpretResult.INTERPRET_RUNTIME_ERROR, instruction, emulator.output


def interpret(emulator, source, debug_level):
    # type: (VM, scanner.Source, int) -> InterpretResultTuple
    """Implement instructions in bytecode."""
    # TODO: Compare implementation for vm.ip in 15.1.1
    fun = compiler.compile(source, debug_level)

    if fun is None:
        fun.bytecode = chunk.free_chunk(bytecode)
        return InterpretResult.INTERPRET_COMPILE_ERROR, None, None

    frame = emulator.frames[emulator.frame_count]
    emulator.frame_count += 1

    emulator = push(emulator, fun)
    frame.fun = fun
    frame.ip = 0
    frame.slots = emulator.stack

    return run(emulator)
