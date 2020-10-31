from typing import Optional

import chunk
import scanner


class Parser():
    def __init__(self):
        # type: () -> None
        """Stores scanner and instructions."""
        self.reader = None  # type: Optional[scanner.Scanner]
        self.bytecode = None  # type: Optional[chunk.Chunk]
        self.current = None  # type: Optional[scanner.Token]
        self.previous = None  # type: Optional[scanner.Token]
        self.had_error = False
        self.panic_mode = False


def init_parser(reader, bytecode):
    # type: (scanner.Scanner, chunk.Chunk) -> Parser
    """Initialize new parser."""
    viewer = Parser()
    viewer.reader = reader
    viewer.bytecode = bytecode

    return viewer


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

        assert viewer.reader is not None
        assert viewer.reader.source is not None
        current_token = viewer.reader.source[token_start:token_end]
        print(" at {}".format(current_token), end=" ")

    return viewer


def error(viewer, message):
    # type: (Parser, str) -> Parser
    """Extract error location from token just consumed."""
    assert viewer.previous is not None
    return error_at(viewer, viewer.previous, message)


def error_at_current(viewer, message):
    # type: (Parser, str) -> Parser
    """Extract error location from current token."""
    assert viewer.current is not None
    return error_at(viewer, viewer.current, message)


def advance(viewer):
    # type: (Parser) -> Parser
    """Steps through token stream and stores for later use."""
    viewer.previous = viewer.current

    while True:
        assert viewer.reader is not None
        viewer.current = scanner.scan_token(viewer.reader)

        if viewer.current.token_type != scanner.TokenType.TOKEN_ERROR:
            break

        # TODO: Check implementation of error message
        viewer = error_at_current(viewer, str(viewer.current.start))

    return viewer


def consume(viewer, token_type, message):
    # type: (Parser, scanner.TokenType, str) -> Parser
    """Reads the next token and validates token has expected type."""
    assert viewer.current is not None
    if viewer.current.token_type == token_type:
        return advance(viewer)

    return error_at_current(viewer, message)


def emit_byte(viewer, byte):
    # type: (Parser, chunk.Byte) -> Parser
    """Append single byte to bytecode."""
    assert viewer.bytecode is not None
    assert viewer.previous is not None
    viewer.bytecode = chunk.write_chunk(viewer.bytecode, byte, viewer.previous.line)

    return viewer


def emit_bytes(viewer, byte1, byte2):
    # type: (Parser, chunk.Byte, chunk.Byte) -> Parser
    """Append two bytes to bytecode."""
    viewer = emit_byte(viewer, byte1)
    return emit_byte(viewer, byte2)


def emit_return(viewer):
    # type: (Parser) -> Parser
    """Clean up after complete compilation stage."""
    return emit_byte(viewer, chunk.OpCode.OP_RETURN)


def end_compiler(viewer):
    # type: (Parser) -> Parser
    """Implement end of expression."""
    return emit_return(viewer)


def compile(source, bytecode):
    # type: (scanner.Source, chunk.Chunk) -> bool
    """Compiles source code into tokens."""
    reader = scanner.init_scanner(source)
    viewer = init_parser(reader, bytecode)

    viewer = advance(viewer)
    expression()
    viewer = consume(viewer, scanner.TokenType.TOKEN_EOF, "Expect end of expression.")
    viewer = end_compiler(viewer)

    return not viewer.had_error
