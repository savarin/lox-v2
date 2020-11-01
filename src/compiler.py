import enum
import functools
from typing import Dict, List, Optional, Tuple

import chunk
import debug
import scanner
import value

UINT8_MAX = 256
UINT8_COUNT = UINT8_MAX + 1


def expose(f):
    """Print the function signature and return value, implemented where function
    returns processor state."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if args[0].debug_level >= 3:
            print("  {}".format(f.__name__))

        value = f(*args, **kwargs)
        return value

    return wrapper


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
    "TOKEN_EQUAL":         [None,       None,     "PREC_NONE"],
    "TOKEN_IDENTIFIER":    [None,       None,     "PREC_NONE"],
    "TOKEN_NUMBER":        ["number",   None,     "PREC_NONE"],
    "TOKEN_FUN":           [None,       None,     "PREC_NONE"],
    "TOKEN_LET":           [None,       None,     "PREC_NONE"],
    "TOKEN_PRINT":         [None,       None,     "PREC_NONE"],
    "TOKEN_RETURN":        [None,       None,     "PREC_NONE"],
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


class Local():
    def __init__(self):
        #
        """
        """
        self.name = None
        self.depth = None


class Compiler():
    def __init__(self):
        #
        """
        """
        self.locals = None
        self.local_count = 0
        self.scope_depth = 0


def init_compiler():
    #
    """
    """
    composer = Compiler()
    composer.locals = [Local() for _ in range(UINT8_COUNT)]

    return composer


class Parser():
    def __init__(self):
        # type: () -> None
        """Stores scanner and instructions."""
        self.searcher = None  # type: Optional[scanner.Scanner]
        self.bytecode = None  # type: Optional[chunk.Chunk]
        self.current = None  # type: Optional[scanner.Token]
        self.previous = None  # type: Optional[scanner.Token]
        self.had_error = False
        self.panic_mode = False
        self.debug_level = 0


def init_parser(searcher, bytecode, debug_level):
    # type: (scanner.Scanner, chunk.Chunk, int) -> Parser
    """Initialize new parser."""
    processor = Parser()
    processor.searcher = searcher
    processor.bytecode = bytecode
    processor.debug_level = debug_level

    return processor


@expose
def error_at(processor, token, message):
    # type: (Parser, scanner.Token, str) -> Parser
    """Expose error and details pertaining to error."""
    if processor.panic_mode:
        return processor

    processor.panic_mode = True

    print("[line {}] Error".format(token.line), end=" ")

    if token.token_type == scanner.TokenType.TOKEN_EOF:
        print("at end")
    elif token.token_type == scanner.TokenType.TOKEN_ERROR:
        pass
    else:
        token_start = token.start
        token_end = token_start + token.length

        assert processor.searcher is not None
        assert processor.searcher.source is not None
        current_token = processor.searcher.source[token_start:token_end]
        print("at {}".format(current_token))

    return processor


@expose
def error(processor, message):
    # type: (Parser, str) -> Parser
    """Extract error location from token just consumed."""
    assert processor.previous is not None
    return error_at(processor, processor.previous, message)


@expose
def error_at_current(processor, message):
    # type: (Parser, str) -> Parser
    """Extract error location from current token."""
    assert processor.current is not None
    return error_at(processor, processor.current, message)


@expose
def advance(processor):
    # type: (Parser) -> Parser
    """Steps through token stream and stores for later use."""
    processor.previous = processor.current

    while True:
        assert processor.searcher is not None

        current_token = scanner.scan_token(processor.searcher)
        processor.current = current_token

        if processor.debug_level >= 2 and current_token.token_type:
            print(current_token.token_type)

        if current_token.token_type != scanner.TokenType.TOKEN_ERROR:
            break

        processor = error_at_current(processor, current_token.source)

    return processor


@expose
def consume(processor, token_type, message):
    # type: (Parser, scanner.TokenType, str) -> Parser
    """Reads the next token and validates token has expected type."""
    assert processor.current is not None
    if processor.current.token_type == token_type:
        return advance(processor)

    return error_at_current(processor, message)


def check(processor, token_type):
    # type: (Parser, scanner.TokenType) -> bool
    """Checks current_token has given type."""
    assert processor.current is not None
    return processor.current.token_type == token_type


@expose
def match(processor, token_type):
    # type: (Parser, scanner.TokenType) -> Tuple[Parser, bool]
    """If current token has given type, consume token and return True."""
    if not check(processor, token_type):
        return processor, False

    return advance(processor), True


@expose
def emit_byte(processor, byte):
    # type: (Parser, chunk.Byte) -> Parser
    """Append single byte to bytecode."""
    assert processor.bytecode is not None
    assert processor.previous is not None
    processor.bytecode = chunk.write_chunk(processor.bytecode, byte, processor.previous.line)

    return processor


@expose
def emit_bytes(processor, byte1, byte2):
    # type: (Parser, chunk.Byte, chunk.Byte) -> Parser
    """Append two bytes to bytecode."""
    processor = emit_byte(processor, byte1)
    return emit_byte(processor, byte2)


@expose
def emit_return(processor):
    # type: (Parser) -> Parser
    """Clean up after complete compilation stage."""
    return emit_byte(processor, chunk.OpCode.OP_RETURN)


@expose
def make_constant(processor, val):
    # type: (Parser, value.Value) -> Tuple[Parser, Optional[value.Value]]
    """Add value to constant table."""
    assert processor.bytecode is not None
    processor.bytecode, constant = chunk.add_constant(processor.bytecode, val)

    if constant > UINT8_MAX:
        return error(processor, "Too many constants in one chunk."), None

    return processor, constant


@expose
def emit_constant(processor, val):
    # type: (Parser, value.Value) -> Parser
    """Append constant to bytecode."""
    processor, constant = make_constant(processor, val)

    assert constant is not None
    return emit_bytes(processor, chunk.OpCode.OP_CONSTANT, constant)


@expose
def end_compiler(processor):
    # type: (Parser) -> Parser
    """Implement end of expression."""
    return emit_return(processor)


@expose
def binary(processor):
    # type: (Parser) -> Parser
    """Implements infix parser for binary operations."""
    # Remember the operator
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the right operand.
    rule = get_rule(processor, operator_type)

    # Get precedence which has 1 priority level above precedence of current rule
    precedence = Precedence(rule.precedence.value + 1)
    parse_precedence(processor, precedence)

    if operator_type == scanner.TokenType.TOKEN_PLUS:
        return emit_byte(processor, chunk.OpCode.OP_ADD)
    elif operator_type == scanner.TokenType.TOKEN_MINUS:
        return emit_byte(processor, chunk.OpCode.OP_SUBTRACT)
    elif operator_type == scanner.TokenType.TOKEN_STAR:
        return emit_byte(processor, chunk.OpCode.OP_MULTIPLY)
    elif operator_type == scanner.TokenType.TOKEN_SLASH:
        return emit_byte(processor, chunk.OpCode.OP_DIVIDE)

    return processor


def expression(processor):
    # type: (Parser) -> None
    """Compiles expression."""
    parse_precedence(processor, Precedence.PREC_ASSIGNMENT)


@expose
def expression_statement(processor):
    # type: (Parser) -> Parser
    """Evaluates expression statement prior to semicolon."""
    expression(processor)

    processor = consume(
        processor,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, chunk.OpCode.OP_POP)


@expose
def print_statement(processor):
    # type: (Parser) -> Parser
    """Evaluates expression and prints result."""
    expression(processor)

    processor = consume(
        processor,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, chunk.OpCode.OP_PRINT)


@expose
def synchronize(processor):
    # type: (Parser) -> Parser
    """Skip tokens until statement boundary reached. This allows multiple errors
    to be exposed, instead of stopping after the first one."""
    processor.panic_mode = False

    assert processor.current is not None
    assert processor.previous is not None

    while processor.current.token_type != scanner.TokenType.TOKEN_EOF:
        if processor.previous.token_type == scanner.TokenType.TOKEN_SEMICOLON:
            break

        elif processor.current.token_type == scanner.TokenType.TOKEN_RETURN:
            break

        processor = advance(processor)

    return processor


@expose
def declaration(processor):
    # type: (Parser) -> Parser
    """Compiles declarations until end of source code reached."""
    processor = statement(processor)

    if processor.panic_mode:
        return synchronize(processor)

    return processor


@expose
def statement(processor):
    # type: (Parser) -> Parser
    """Handler for statements."""
    processor, condition = match(processor, scanner.TokenType.TOKEN_PRINT)

    if condition:
        return print_statement(processor)

    return expression_statement(processor)


@expose
def grouping(processor):
    # type: (Parser) -> Parser
    """Compiles expression between parentheses and consumes parentheses."""
    expression(processor)
    return consume(processor, scanner.TokenType.TOKEN_RIGHT_PAREN, "Expect ')' after expression.")


@expose
def number(processor):
    # type: (Parser) -> Parser
    """Append number literal to bytecode."""
    assert processor.previous is not None
    assert processor.previous.source is not None
    val = float(processor.previous.source)

    return emit_constant(processor, val)


@expose
def unary(processor):
    # type: (Parser) -> Parser
    """Comsumes leading minus and appends negated value."""
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the operand
    parse_precedence(processor, Precedence.PREC_UNARY)

    # Emit the operator instruction
    if operator_type == scanner.TokenType.TOKEN_MINUS:
        processor = emit_byte(processor, chunk.OpCode.OP_NEGATE)

    return processor


def parse_precedence(processor, precedence):
    # type: (Parser, Precedence) -> None
    """Starts at current token and parses expression at given precedence level
    or higher."""
    processor = advance(processor)

    assert processor.previous is not None
    prefix_rule = get_rule(processor, processor.previous.token_type).prefix

    if prefix_rule is None:
        error(processor, "Expect expression")
        return None

    prefix_rule(processor)

    assert processor.current is not None
    while precedence.value <= get_rule(processor, processor.current.token_type).precedence.value:
        processor = advance(processor)

        assert processor.previous is not None
        infix_rule = get_rule(processor, processor.previous.token_type).infix

        infix_rule(processor)


def get_rule(processor, token_type):
    # type: (Parser, scanner.TokenType) -> ParseRule
    """Custom function to convert TokenType to ParseRule. This allows the
    rule_map to consist of strings, which are then replaced by respective
    classes in the conversion process."""
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


def compile(source, bytecode, debug_level):
    # type: (scanner.Source, chunk.Chunk, int) -> bool
    """Compiles source code into tokens."""
    searcher = scanner.init_scanner(source)
    processor = init_parser(searcher, bytecode, debug_level)

    if debug_level >= 2:
        print("\n== tokens ==")

    processor = advance(processor)

    while True:
        processor, condition = match(processor, scanner.TokenType.TOKEN_EOF)

        if condition:
            break

        processor = declaration(processor)
        # processor = expression(processor)

    processor = end_compiler(processor)

    if debug_level >= 1:
        assert processor.bytecode is not None
        debug.disassemble_chunk(processor.bytecode, "script")

    return not processor.had_error
