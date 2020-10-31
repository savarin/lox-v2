import sys

import vm


def main():
    # type: () -> None
    """Set up REPL or compile from file based on arguments."""
    emulator = vm.init_vm()
    size = len(sys.argv)

    if size == 1:
        repl(emulator)
    elif size == 2:
        read_file(emulator, sys.argv[1])
    else:
        print("Usage: clox [path]")
        exit_code(64)

    emulator = vm.free_vm(emulator)


def repl(emulator):
    # type: (vm.VM) -> None
    """Set up REPL for custom code input."""
    while True:
        line = input("> ")

        if not line:
            print("")
            break

        # TODO: Revisit once scanner complete
        vm.interpret(emulator, line)  # type: ignore


def read_file(emulator, path):
    # type: (vm.VM, str) -> None
    """Compile and run source code in file at path."""
    with open(path, "r") as f:
        source = f.read()

    # TODO: Revisit once scanner complete
    result, constant = vm.interpret(emulator, source)  # type: ignore

    if result == vm.InterpretResult.INTERPRET_COMPILE_ERROR:
        exit_code(65)

    elif result == vm.InterpretResult.INTERPRET_RUNTIME_ERROR:
        exit_code(70)


def exit_code(error_code):
    # type: (int) -> None
    print("Exit: {}".format(error_code))
    sys.exit()


if __name__ == "__main__":
    main()
