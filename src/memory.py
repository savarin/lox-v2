from typing import Any, List, Optional


def grow_capacity(capacity):
    # type: (int) -> int
    """Calculates new capacity based on given current capacity."""
    if capacity < 8:
        return 8

    return capacity * 2


def grow_array(array, old_count, new_count):
    # type: (Optional[List[Any]], int, int) -> Optional[List[Any]]
    """Wrapper around reallocate call to grow size of array."""
    return reallocate(array, old_count, new_count)


def free_array(array, old_count):
    # type: (Optional[List[Any]], int) -> Optional[List[Any]]
    """Frees memory."""
    return reallocate(array, old_count, 0)


def reallocate(array, old_size, new_size):
    # type: (Optional[List[Any]], int, int) -> Optional[List[Any]]
    """Handles all dynamic memory management, including allocating memory,
    freeing it and changing the size of an existing allocation."""
    if new_size == 0:
        return None

    # Create empty list if array is None
    array = array or []

    for i in range(new_size - old_size):
        array.append(None)

    return array
