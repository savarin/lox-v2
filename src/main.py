import sys

import vm


def repl(emulator):
    # type: (vm.VM) -> None
    """Set up REPL for custom code input."""
    while True:
        line = input("> ")

        if not line:
            print("")
            break

        vm.interpret(emulator, line, 0)


def read_file(emulator, path, debug_level=0):
    # type: (vm.VM, str, int) -> None
    """Compile and run source code in file at path."""
    with open(path, "r") as f:
        source = f.read()

    interpret_result, _, _ = vm.interpret(emulator, source, debug_level)

    if interpret_result == vm.InterpretResult.INTERPRET_COMPILE_ERROR:
        exit_code(65)

    elif interpret_result == vm.InterpretResult.INTERPRET_RUNTIME_ERROR:
        exit_code(70)


def exit_code(error_code):
    # type: (int) -> None
    """Expose error code and exit."""
    print("Exit: {}".format(error_code))
    sys.exit()


def main():
    # type: () -> None
    """Set up REPL or compile from file based on arguments."""
    emulator = vm.init_vm()
    size = len(sys.argv)

    if size == 1:
        repl(emulator)
    elif size == 2:
        read_file(emulator, sys.argv[1])
    elif size == 3:
        read_file(emulator, sys.argv[1], int(sys.argv[2]))
    else:
        print("Usage: python src/main.py [path]")
        exit_code(64)

    vm.free_vm(emulator)


if __name__ == "__main__":
    main()
