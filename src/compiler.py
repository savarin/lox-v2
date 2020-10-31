import enum
from typing import Dict, List, Optional, Tuple

import chunk
import scanner
import value

UINT8_MAX = 256

# yapf: disable
rule_map = {
    "TOKEN_LEFT_PAREN":    ["grouping", None,     "PREC_NONE"],
    "TOKEN_RIGHT_PAREN":   [None,       None,     "PREC_NONE"],
    "TOKEN_LEFT_BRACE":    [None,       None,     "PREC_NONE"],
    "TOKEN_RIGHT_BRACE":   [None,       None,     "PREC_NONE"],
    "TOKEN_MINUS":         ["unary",    "binary", "PREC_TERM"],
    "TOKEN_PLUS":          [None,       "binary", "PREC_TERM"],
    "TOKEN_SEMICOLON":     [None,       None,     "PREC_NONE"],
    "TOKEN_SLASH":         [None,       "binary", "PREC_FACTOR"],
    "TOKEN_STAR":          [None,       "binary", "PREC_FACTOR"],
    "TOKEN_BANG":          [None,       None,     "PREC_NONE"],
    "TOKEN_BANG_EQUAL":    [None,       None,     "PREC_NONE"],
    "TOKEN_EQUAL":         [None,       None,     "PREC_NONE"],
    "TOKEN_EQUAL_EQUAL":   [None,       None,     "PREC_NONE"],
    "TOKEN_GREATER":       [None,       None,     "PREC_NONE"],
    "TOKEN_GREATER_EQUAL": [None,       None,     "PREC_NONE"],
    "TOKEN_LESS":          [None,       None,     "PREC_NONE"],
    "TOKEN_LESS_EQUAL":    [None,       None,     "PREC_NONE"],
    "TOKEN_IDENTIFIER":    [None,       None,     "PREC_NONE"],
    "TOKEN_STRING":        [None,       None,     "PREC_NONE"],
    "TOKEN_NUMBER":        ["number",   None,     "PREC_NONE"],
    "TOKEN_FALSE":         [None,       None,     "PREC_NONE"],
    "TOKEN_FUN":           [None,       None,     "PREC_NONE"],
    "TOKEN_PRINT":         [None,       None,     "PREC_NONE"],
    "TOKEN_RETURN":        [None,       None,     "PREC_NONE"],
    "TOKEN_TRUE":          [None,       None,     "PREC_NONE"],
    "TOKEN_VAR":           [None,       None,     "PREC_NONE"],
    "TOKEN_ERROR":         [None,       None,     "PREC_NONE"],
    "TOKEN_EOF":           [None,       None,     "PREC_NONE"],
}  # type: Dict[str, List[Optional[str]]]


class Precedence(enum.Enum):
    PREC_NONE = 1
    PREC_ASSIGNMENT = 2  # =
    PREC_EQUALITY = 3    # == !=
    PREC_COMPARISON = 4  # < > <= >=
    PREC_TERM = 5        # + -
    PREC_FACTOR = 6      # * /
    PREC_UNARY = 7       # ! -
    PREC_CALL = 8        # ()
    PREC_PRIMARY = 9
# yapf: enable


class ParseRule():
    def __init__(self, prefix, infix, precedence):
        #
        """Wrapper for precedence rule."""
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence


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
    resolver = Parser()
    resolver.reader = reader
    resolver.bytecode = bytecode

    return resolver


def error_at(resolver, token, message):
    # type: (Parser, scanner.Token, str) -> Parser
    """Expose error and details pertaining to error."""
    if resolver.panic_mode:
        return resolver

    resolver.panic_mode = True

    print("[line {}] Error".format(token.line), end=" ")

    if token.token_type == scanner.TokenType.TOKEN_EOF:
        print("at end", end=" ")
    elif token.token_type == scanner.TokenType.TOKEN_ERROR:
        pass
    else:
        token_start = token.start
        token_end = token_start + token.length

        assert resolver.reader is not None
        assert resolver.reader.source is not None
        current_token = resolver.reader.source[token_start:token_end]
        print("at {}".format(current_token), end=" ")

    return resolver


def error(resolver, message):
    # type: (Parser, str) -> Parser
    """Extract error location from token just consumed."""
    assert resolver.previous is not None
    return error_at(resolver, resolver.previous, message)


def error_at_current(resolver, message):
    # type: (Parser, str) -> Parser
    """Extract error location from current token."""
    assert resolver.current is not None
    return error_at(resolver, resolver.current, message)


def advance(resolver):
    # type: (Parser) -> Parser
    """Steps through token stream and stores for later use."""
    resolver.previous = resolver.current

    while True:
        assert resolver.reader is not None
        current_token = scanner.scan_token(resolver.reader)
        resolver.current = current_token

        if current_token.token_type:
            print(current_token.token_type)

        if current_token.token_type != scanner.TokenType.TOKEN_ERROR:
            break

        # TODO: Check implementation of error message
        resolver = error_at_current(resolver, str(current_token.start))

    return resolver


def consume(resolver, token_type, message):
    # type: (Parser, scanner.TokenType, str) -> Parser
    """Reads the next token and validates token has expected type."""
    assert resolver.current is not None
    if resolver.current.token_type == token_type:
        return advance(resolver)

    return error_at_current(resolver, message)


def emit_byte(resolver, byte):
    # type: (Parser, chunk.Byte) -> Parser
    """Append single byte to bytecode."""
    assert resolver.bytecode is not None
    assert resolver.previous is not None
    resolver.bytecode = chunk.write_chunk(resolver.bytecode, byte, resolver.previous.line)

    return resolver


def emit_bytes(resolver, byte1, byte2):
    # type: (Parser, chunk.Byte, chunk.Byte) -> Parser
    """Append two bytes to bytecode."""
    resolver = emit_byte(resolver, byte1)
    return emit_byte(resolver, byte2)


def emit_return(resolver):
    # type: (Parser) -> Parser
    """Clean up after complete compilation stage."""
    return emit_byte(resolver, chunk.OpCode.OP_RETURN)


def make_constant(resolver, val):
    # type: (Parser, value.Value) -> Tuple[Parser, Optional[value.Value]]
    """Add value to constant table."""
    assert resolver.bytecode is not None
    resolver.bytecode, constant = chunk.add_constant(resolver.bytecode, val)

    if constant > UINT8_MAX:
        return error(resolver, "Too many constants in one chunk."), None

    return resolver, constant


def emit_constant(resolver, val):
    # type: (Parser, value.Value) -> Parser
    """Append constant to bytecode."""
    resolver, constant = make_constant(resolver, val)

    assert constant is not None
    return emit_bytes(resolver, chunk.OpCode.OP_CONSTANT, constant)


def end_compiler(resolver):
    # type: (Parser) -> Parser
    """Implement end of expression."""
    return emit_return(resolver)


def binary(resolver):
    # type: (Parser) -> Parser
    """Implements infix parser for binary operations."""
    # Remember the operator
    assert resolver.previous is not None
    operator_type = resolver.previous.token_type

    # Compile the right operand.
    rule = get_rule(resolver, operator_type)

    # Get precedence which has 1 priority level above precedence of current rule
    precedence = Precedence(rule.precedence.value + 1)
    parse_precedence(resolver, precedence)

    if operator_type == scanner.TokenType.TOKEN_PLUS:
        return emit_byte(resolver, chunk.OpCode.OP_ADD)
    elif operator_type == scanner.TokenType.TOKEN_MINUS:
        return emit_byte(resolver, chunk.OpCode.OP_SUBTRACT)
    elif operator_type == scanner.TokenType.TOKEN_STAR:
        return emit_byte(resolver, chunk.OpCode.OP_MULTIPLY)
    elif operator_type == scanner.TokenType.TOKEN_SLASH:
        return emit_byte(resolver, chunk.OpCode.OP_DIVIDE)

    return resolver


def expression(resolver):
    #
    """
    """
    parse_precedence(resolver, Precedence.PREC_ASSIGNMENT)


def grouping(resolver):
    # type: (Parser) -> Parser
    """Compiles expression between parentheses and consumes parentheses."""
    expression(resolver)
    return consume(resolver, scanner.TokenType.TOKEN_RIGHT_PAREN, "Expect ')' after expression.")


def number(resolver):
    # type: (Parser) -> Parser
    """Append number literal to bytecode."""
    assert resolver.previous is not None
    val = float(resolver.previous.start)
    return emit_constant(resolver, val)


def unary(resolver):
    # type: (Parser) -> Parser
    """Comsumes leading minus and appends negated value."""
    assert resolver.previous is not None
    operator_type = resolver.previous.token_type

    # Compile the operand
    parse_precedence(resolver, Precedence.PREC_UNARY)

    # Emit the operator instruction
    if operator_type == scanner.TokenType.TOKEN_MINUS:
        resolver = emit_byte(resolver, chunk.OpCode.OP_NEGATE)

    return resolver


def parse_precedence(resolver, precedence):
    # type: (Parser, Precedence) -> None
    """Starts at current token and parses expression at given precedence level
    or higher."""
    resolver = advance(resolver)

    assert resolver.previous is not None
    prefix_rule = get_rule(resolver, resolver.previous.token_type).prefix

    if prefix_rule is None:
        error(resolver, "Expect expression")
        return None

    prefix_rule(resolver)

    assert resolver.current is not None
    while precedence.value <= get_rule(resolver, resolver.current.token_type).precedence.value:
        resolver = advance(resolver)

        assert resolver.previous is not None
        infix_rule = get_rule(resolver, resolver.previous.token_type).infix

        infix_rule(resolver)


def get_rule(resolver, token_type):
    # type: (Parser, scanner.TokenType) -> ParseRule
    """Custom function to convert TokenType to ParseRule. This allows the
    rule_map to consist of strings, which are then replaced by respective
    classes in the conversion process.
    """
    type_map = {
        "binary": binary,
        "grouping": grouping,
        "number": number,
        "unary": unary,
    }

    rule = rule_map[token_type.name]

    assert rule[2] is not None
    return ParseRule(
        prefix=None if rule[0] is None else type_map[rule[0]],
        infix=None if rule[1] is None else type_map[rule[1]],
        precedence=Precedence[rule[2]],
    )


def compile(source, bytecode):
    # type: (scanner.Source, chunk.Chunk) -> bool
    """Compiles source code into tokens."""
    reader = scanner.init_scanner(source)
    resolver = init_parser(reader, bytecode)

    resolver = advance(resolver)

    # breakpoint()
    # print(source)
    # import sys; sys.exit()

    expression(resolver)
    resolver = consume(resolver, scanner.TokenType.TOKEN_EOF, "Expect end of expression.")
    resolver = end_compiler(resolver)

    return not resolver.had_error
