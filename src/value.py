from typing import List, Optional, Union

import memory

Value = Union[int, float]
Values = Optional[List[Optional[Value]]]


class ValueArray():
    def __init__(self):
        # type: () -> None
        """Wraps array with allocated capacity and number of elements in use."""
        self.count = 0
        self.capacity = 0
        self.values = None  # type: Values


def init_value_array():
    # type: () -> ValueArray
    """Initialize new value array."""
    return ValueArray()


def free_value_array(value_array):
    # type: (ValueArray) -> ValueArray
    """Deallocates memory and calls init_value_array to leave value array in a
    well-defined empty state."""
    assert value_array.values is not None
    value_array.values = memory.free_array(value_array.values, value_array.capacity)
    value_array.count = 0
    value_array.capacity = 0

    return init_value_array()


def write_value_array(value_array, val):
    # type: (ValueArray, Value) -> ValueArray
    """Append value to the end of the value array."""
    # If current array not have capacity for new value, grow array.
    if value_array.capacity < value_array.count + 1:
        old_capacity = value_array.capacity
        value_array.capacity = memory.grow_capacity(old_capacity)
        value_array.values = memory.grow_array(
            value_array.values,
            old_capacity,
            value_array.capacity,
        )

    assert value_array.values is not None
    value_array.values[value_array.count] = val
    value_array.count += 1

    return value_array


def print_value(val):
    # type: (Value) -> None
    """Print value based on value type."""
    print(val)
