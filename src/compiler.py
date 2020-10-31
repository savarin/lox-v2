import chunk
import scanner


class Parser():
    def __init__(self, reader):
        #
        """
        """
        self.reader = reader
        self.current = None
        self.previous = None
        self.had_error = False
        self.panic_mode = False


def error_at(viewer, token, message):
    # type: (Parser, scanner.Token, str) -> Parser
    """Expose error and details pertaining to error."""
    if viewer.panic_mode:
        return viewer

    viewer.panic_mode = True

    print("[line {}] Error".format(token.line), end=" ")

    if token.token_type == scanner.TokenType.TOKEN_EOF:
        print(" at end", end=" ")
    elif token.token_type == scanner.TokenType.TOKEN_ERROR:
        pass
    else:
        token_start = token.start
        token_end = token_start + token.length

        current_token = viewer.reader.source[token_start:token_end]
        print(" at {}".format(current_token), end=" ")

    return viewer


def error(viewer, message):
    # type: (Parser, str) -> Parser
    """Extract error location from token just consumed."""
    return error_at(viewer, viewer.previous, message)


def error_at_current(viewer, message):
    # type: (Parser, str) -> Parser
    """Extract error location from current token."""
    return error_at(viewer, viewer.current, message)


def advance(viewer):
    # type: (Parser) -> Parser
    """Steps through token stream and stores for later use."""
    viewer.previous = viewer.current

    while True:
        viewer.current = scanner.scan_token(viewer.reader)

        if viewer.current.token_type != scanner.TokenType.TOKEN_ERROR:
            break

        # TODO: Check implementation of error message
        viewer = error_at_current(viewer, str(viewer.current.start))

    return viewer


def consume(viewer, token_type, message):
    # type: (Parser, scanner.TokenType, str) -> Parser
    """Reads the next token and validates token has expected type."""
    if viewer.current.token_type == token_type:
        return advance(viewer)

    return error_at_current(viewer, message)


def compile(source, bytecode):
    # type: (scanner.Source, chunk.Chunk) -> bool
    """Compiles source code into tokens."""
    reader = scanner.init_scanner(source)
    viewer = Parser(reader)

    viewer = advance(viewer)
    expression()
    viewer = consume(viewer, scanner.TokenType.TOKEN_EOF, "Expect end of expression.")

    return not viewer.had_error
