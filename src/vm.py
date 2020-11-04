import enum
from typing import List, Optional, Tuple, Union

import chunk
import compiler
import function
import scanner
import value

FRAMES_MAX = 8
STACK_MAX = 8

InterpretResultTuple = Tuple["InterpretResult", Optional[chunk.OpCode], Optional[List[value.Value]]]
StackItem = Union[value.Value, value.ValueType, function.Function]


class InterpretResult(enum.Enum):
    INTERPRET_OK = "INTERPRET_OK"
    INTERPRET_COMPILE_ERROR = "INTERPRET_COMPILE_ERROR"
    INTERPRET_RUNTIME_ERROR = "INTERPRET_RUNTIME_ERROR"


class CallFrame():
    def __init__(self, fun, ip, slots, slots_top):
        # type: (Optional[function.Function], int, Optional[List[Optional[StackItem]]], int) -> None
        """Stores function and function slots."""
        self.fun = fun
        self.ip = ip
        self.slots = slots
        self.slots_top = slots_top


class VM():
    def __init__(self):
        # type: () -> None
        """Stores call frames and stack."""
        self.frames = None  # type: Optional[List[CallFrame]]
        self.frame_count = 0
        self.stack = None  # type: Optional[List[Optional[StackItem]]]
        self.stack_top = 0
        self.counter = 0
        self.output = None  # type: Optional[List[value.Value]]


def reset_stack(emulator):
    # type: (VM) -> VM
    """Reset VM by moving stack_top to point to beginning of array, thus
    indicating stack is empty."""
    emulator.frames = [CallFrame(None, 0, None, 0) for _ in range(FRAMES_MAX)]
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
        assert emulator.frames is not None
        frame = emulator.frames[i]

        assert frame.fun is not None
        bytecode = frame.fun.bytecode

        assert bytecode is not None
        if bytecode.code is not None:
            chunk.free_chunk(bytecode)

    return reset_stack(emulator)


def push(frame, val):
    # type: (CallFrame, StackItem) -> CallFrame
    """Push new value to the top of the stack."""
    assert frame.slots is not None
    frame.slots[frame.slots_top] = val
    frame.slots_top += 1

    return frame

    # assert emulator.stack is not None
    # emulator.stack[emulator.stack_top] = val
    # emulator.stack_top += 1

    # return emulator


def pop(frame):
    # type: (CallFrame) -> Tuple[CallFrame, StackItem]
    """Pop most recently pushed value."""
    frame.slots_top -= 1
    assert frame.slots is not None
    val = frame.slots[frame.slots_top]

    assert val is not None
    return frame, val

    # emulator.stack_top -= 1

    # assert emulator.stack is not None
    # val = emulator.stack[emulator.stack_top]

    # assert val is not None
    # return emulator, val


def peek(frame, distance):
    # type: (CallFrame, int) -> Tuple[CallFrame, StackItem]
    """Reads value but does not pop it."""
    assert frame.slots is not None
    val = frame.slots[frame.slots_top - 1 - distance]

    assert val is not None
    return frame, val

    # assert emulator.stack is not None
    # val = emulator.stack[emulator.stack_top - 1 - distance]

    # assert val is not None
    # return emulator, val


def call(emulator, fun, arg_count):
    # type: (VM, function.Function, int) -> Tuple[VM, bool]
    """
    """
    # Number of arguments not as expected
    if arg_count != fun.arity:
        return emulator, False

    # Stack overflow
    if emulator.frame_count == FRAMES_MAX:
        return emulator, False

    assert emulator.frames is not None
    frame = emulator.frames[emulator.frame_count]
    emulator.frame_count += 1

    # TODO: Compare implementation of ip in 24.5
    frame.fun = fun
    frame.ip = 0
    frame.slots_top = arg_count + 1
    assert emulator.stack is not None
    frame.slots = emulator.stack[emulator.stack_top - frame.slots_top:]

    return emulator, True


def call_value(emulator, fun, arg_count):
    # type: (VM, function.Function, int) -> Tuple[VM, bool]
    """
    """
    if getattr(fun, "function_type", None) is not None:
        return call(emulator, fun, arg_count)

    return emulator, False


def read_byte(frame):
    # type: (CallFrame) -> Tuple[CallFrame, chunk.Byte]
    """Reads byte at current instruction pointer and advances pointer."""
    frame.ip += 1

    assert frame.fun is not None
    assert frame.fun.bytecode is not None
    assert frame.fun.bytecode.code is not None
    instruction = frame.fun.bytecode.code[frame.ip - 1]

    assert instruction is not None
    return frame, instruction


def read_constant(frame):
    # type: (CallFrame) -> Tuple[CallFrame, StackItem]
    """Reads next byte from bytecode, treats result as index and looks up
    corresponding location in constants table."""
    frame, offset = read_byte(frame)

    assert frame.fun is not None
    assert frame.fun.bytecode is not None
    assert frame.fun.bytecode.constants is not None
    assert frame.fun.bytecode.constants.values is not None
    assert isinstance(offset, int)
    constant = frame.fun.bytecode.constants.values[offset]

    assert constant is not None
    return frame, constant


def binary_op(frame, op):
    # type: (CallFrame, str) -> CallFrame
    """Execute binary operation on two items at the top of the stack."""
    frame, b = pop(frame)
    frame, a = pop(frame)

    return push(frame, eval("a {} b".format(op)))


def run(emulator):
    # type: (VM) -> InterpretResultTuple
    """Executes instructions in bytecode."""
    assert emulator.frames is not None
    frame = emulator.frames[emulator.frame_count - 1]

    while True:
        frame, instruction = read_byte(frame)

        if instruction == chunk.OpCode.OP_CONSTANT:
            frame, constant = read_constant(frame)
            frame = push(frame, constant)

        elif instruction == chunk.OpCode.OP_NIL:
            frame = push(frame, value.ValueType.VAL_NIL)

        elif instruction == chunk.OpCode.OP_POP:
            frame, _ = pop(frame)

        elif instruction == chunk.OpCode.OP_GET_LOCAL:
            frame, slot = read_byte(frame)
            assert frame.slots is not None
            assert isinstance(slot, int)
            val = frame.slots[slot]
            if val is None:
                break
            frame = push(frame, val)

        elif instruction == chunk.OpCode.OP_SET_LOCAL:
            frame, slot = read_byte(frame)
            frame, val = peek(frame, 0)
            assert frame.slots is not None
            assert isinstance(slot, int)
            frame.slots[slot] = val

        elif instruction == chunk.OpCode.OP_ADD:
            frame = binary_op(frame, "+")

        elif instruction == chunk.OpCode.OP_SUBTRACT:
            frame = binary_op(frame, "-")

        elif instruction == chunk.OpCode.OP_MULTIPLY:
            frame = binary_op(frame, "*")

        elif instruction == chunk.OpCode.OP_DIVIDE:
            frame = binary_op(frame, "/")

        elif instruction == chunk.OpCode.OP_NEGATE:
            frame, val = pop(frame)
            assert not isinstance(val, function.Function)
            assert not isinstance(val, value.ValueType)
            val = -val
            frame = push(frame, val)

        elif instruction == chunk.OpCode.OP_PRINT:
            frame, val = pop(frame)
            assert not isinstance(val, function.Function)
            assert not isinstance(val, value.ValueType)
            assert emulator.output is not None
            emulator.output.append(val)

        elif instruction == chunk.OpCode.OP_CALL:
            frame, arg_count = read_byte(frame)
            assert isinstance(arg_count, int)
            frame, fun = peek(frame, arg_count)
            assert isinstance(fun, function.Function)
            emulator, condition = call_value(emulator, fun, arg_count)
            if not condition:
                break
            assert emulator.frames is False
            frame = emulator.frames[emulator.frame_count - 1]

        elif instruction == chunk.OpCode.OP_RETURN:
            frame, result = pop(frame)
            emulator.frame_count -= 1
            if emulator.frame_count == 0:
                frame, result = pop(frame)
                assert isinstance(instruction, chunk.OpCode)
                return InterpretResult.INTERPRET_OK, instruction, emulator.output
            frame = push(frame, result)
            assert emulator.frames is not None
            frame = emulator.frames[emulator.frame_count - 1]

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
        return InterpretResult.INTERPRET_COMPILE_ERROR, None, None

    # emulator = push(emulator, fun)
    assert emulator.stack is not None
    emulator.stack[emulator.stack_top] = fun
    emulator.stack_top += 1

    emulator, condition = call_value(emulator, fun, 0)

    return run(emulator)
