import enum
import functools
from typing import Callable, Dict, List, Optional, Tuple

import chunk
import debug
import scanner
import value

UINT8_MAX = 8
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
    "TOKEN_IDENTIFIER":    ["variable", None,     "PREC_NONE"],
    "TOKEN_NUMBER":        ["number",   None,     "PREC_NONE"],
    "TOKEN_FUN":           [None,       None,     "PREC_NONE"],
    "TOKEN_PRINT":         [None,       None,     "PREC_NONE"],
    "TOKEN_RETURN":        [None,       None,     "PREC_NONE"],
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
        # type: (Optional[Callable], Optional[Callable], Precedence) -> None
        """Wrapper for precedence rule."""
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence


class Local():
    def __init__(self):
        # type: () -> None
        """Stores token and state of lexical scope."""
        self.token = None  # type: Optional[scanner.Token]
        self.depth = 0


class Compiler():
    def __init__(self):
        # type: () -> None
        """Stores local variables, count and scope depth."""
        self.locals = None  # type: Optional[List[Local]]
        self.local_count = 0
        self.scope_depth = 0


def init_compiler():
    # type: () -> Compiler
    """Initialize new compiler."""
    composer = Compiler()
    composer.locals = [Local() for _ in range(UINT8_COUNT)]

    return composer


class Parser():
    def __init__(self):
        # type: () -> None
        """Stores scanner and instructions."""
        self.current = None  # type: Optional[scanner.Token]
        self.previous = None  # type: Optional[scanner.Token]
        self.had_error = False
        self.panic_mode = False
        self.debug_level = 0


def init_parser(debug_level):
    # type: (int) -> Parser
    """Initialize new parser."""
    processor = Parser()
    processor.debug_level = debug_level

    return processor


@expose
def error_at(processor, searcher, token, message):
    # type: (Parser, scanner.Scanner, scanner.Token, str) -> Parser
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
        assert searcher.source is not None
        current_token = searcher.source[token.start:token.start + token.length]
        print("at {}".format(current_token))

    return processor


@expose
def error(processor, searcher, message):
    # type: (Parser, scanner.Scanner, str) -> Parser
    """Extract error location from token just consumed."""
    return error_at(processor, searcher, processor.previous, message)


@expose
def error_at_current(processor, searcher, message):
    # type: (Parser, scanner.Scanner, str) -> Parser
    """Extract error location from current token."""
    return error_at(processor, searcher, processor.current, message)


@expose
def advance(processor, searcher):
    # type: (Parser, scanner.Scanner) -> Parser
    """Steps through token stream and stores for later use."""
    processor.previous = processor.current

    while True:
        current_token = scanner.scan_token(searcher)
        processor.current = current_token

        if processor.debug_level >= 2 and current_token.token_type:
            print(current_token.token_type)

        if current_token.token_type != scanner.TokenType.TOKEN_ERROR:
            break

        processor = error_at_current(processor, searcher, current_token.source)

    return processor


@expose
def consume(processor, searcher, token_type, message):
    # type: (Parser, scanner.Scanner, scanner.TokenType, str) -> Parser
    """Reads the next token and validates token has expected type."""
    assert processor.current is not None
    if processor.current.token_type == token_type:
        return advance(processor, searcher)

    return error_at_current(processor, searcher, message)


def check(processor, token_type):
    # type: (Parser, scanner.TokenType) -> bool
    """Checks current_token has given type."""
    assert processor.current is not None
    return processor.current.token_type == token_type


def match(processor, searcher, token_type):
    # type: (Parser, scanner.Scanner, scanner.TokenType) -> Tuple[Parser, bool]
    """If current token has given type, consume token and return True."""
    if not check(processor, token_type):
        return processor, False

    return advance(processor, searcher), True


@expose
def emit_byte(processor, bytecode, byte):
    # type: (Parser, chunk.Chunk, chunk.Byte) -> Tuple[Parser, chunk.Chunk]
    """Append single byte to bytecode."""
    assert processor.previous is not None
    bytecode = chunk.write_chunk(bytecode, byte, processor.previous.line)

    return processor, bytecode


@expose
def emit_bytes(processor, bytecode, byte1, byte2):
    # type: (Parser, chunk.Chunk, chunk.Byte, chunk.Byte) -> Tuple[Parser, chunk.Chunk]
    """Append two bytes to bytecode."""
    processor, bytecode = emit_byte(processor, bytecode, byte1)
    return emit_byte(processor, bytecode, byte2)


@expose
def emit_return(processor, bytecode):
    # type: (Parser, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Clean up after complete compilation stage."""
    return emit_byte(processor, bytecode, chunk.OpCode.OP_RETURN)


@expose
def make_constant(processor, searcher, bytecode, val):
    # type: (Parser, scanner.Scanner, chunk.Chunk, value.Value) -> Tuple[Parser, Optional[value.Value]]
    """Add value to constant table."""
    bytecode, constant = chunk.add_constant(bytecode, val)

    if constant > UINT8_MAX:
        return error(processor, searcher, "Too many constants in one chunk."), None

    return processor, constant


@expose
def emit_constant(processor, searcher, bytecode, val):
    # type: (Parser, scanner.Scanner, chunk.Chunk, value.Value) -> Tuple[Parser, chunk.Chunk]
    """Append constant to bytecode."""
    processor, constant = make_constant(processor, searcher, bytecode, val)

    assert constant is not None
    return emit_bytes(processor, bytecode, chunk.OpCode.OP_CONSTANT, constant)


@expose
def end_compiler(processor, bytecode):
    # type: (Parser, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Implement end of expression."""
    return emit_return(processor, bytecode)


@expose
def begin_scope(processor, composer):
    # type: (Parser, Compiler) -> Compiler
    """Enter a new local scope."""
    composer.scope_depth += 1
    return composer


@expose
def end_scope(processor, composer, bytecode):
    # type: (Parser, Compiler, chunk.Chunk) -> Tuple[Parser, Compiler, chunk.Chunk]
    """Exit local scope."""
    composer.scope_depth -= 1

    while True:
        is_positive = composer.local_count > 0

        assert composer.locals is not None
        depth = composer.locals[composer.local_count - 1].depth
        is_over_scope = depth > composer.scope_depth

        if not is_positive or not is_over_scope:
            break

        processor, bytecode = emit_byte(processor, bytecode, chunk.OpCode.OP_POP)
        composer.local_count -= 1

    return processor, composer, bytecode


@expose
def binary(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Implements infix parser for binary operations."""
    # Remember the operator
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the right operand.
    rule = get_rule(operator_type)

    # Get precedence which has 1 priority level above precedence of current rule
    precedence = Precedence(rule.precedence.value + 1)
    processor, bytecode = parse_precedence(processor, composer, searcher, bytecode, precedence)

    if operator_type == scanner.TokenType.TOKEN_PLUS:
        return emit_byte(processor, bytecode, chunk.OpCode.OP_ADD)
    elif operator_type == scanner.TokenType.TOKEN_MINUS:
        return emit_byte(processor, bytecode, chunk.OpCode.OP_SUBTRACT)
    elif operator_type == scanner.TokenType.TOKEN_STAR:
        return emit_byte(processor, bytecode, chunk.OpCode.OP_MULTIPLY)
    elif operator_type == scanner.TokenType.TOKEN_SLASH:
        return emit_byte(processor, bytecode, chunk.OpCode.OP_DIVIDE)

    return processor, bytecode


@expose
def expression(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Compiles expression."""
    return parse_precedence(processor, composer, searcher, bytecode, Precedence.PREC_ASSIGNMENT)


@expose
def block(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, Compiler, chunk.Chunk]
    """Compile block within scope."""
    while True:
        is_right_brace = check(processor, scanner.TokenType.TOKEN_RIGHT_BRACE)
        is_eof = check(processor, scanner.TokenType.TOKEN_EOF)

        if is_right_brace or is_eof:
            break

        processor, composer, bytecode = declaration(processor, composer, searcher, bytecode)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_RIGHT_BRACE,
        "Expect '}' after block.",
    )

    return processor, composer, bytecode


@expose
def variable_declaration(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, Compiler, chunk.Chunk]
    """Declare variable when corresponding token matched."""
    processor, _ = parse_variable(processor, composer, searcher, bytecode, "Expect variable name.")
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_EQUAL)

    assert condition
    processor, bytecode = expression(processor, composer, searcher, bytecode)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after variable declaration.",
    )

    composer = define_variable(processor, composer)

    return processor, composer, bytecode


@expose
def expression_statement(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Evaluates expression statement prior to semicolon."""
    processor, bytecode = expression(processor, composer, searcher, bytecode)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, bytecode, chunk.OpCode.OP_POP)


@expose
def print_statement(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Evaluates expression and prints result."""
    processor, bytecode = expression(processor, composer, searcher, bytecode)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, bytecode, chunk.OpCode.OP_PRINT)


@expose
def synchronize(processor, searcher):
    # type: (Parser, scanner.Scanner) -> Parser
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

        processor = advance(processor, searcher)

    return processor


@expose
def declaration(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, Compiler, chunk.Chunk]
    """Compiles declarations until end of source code reached."""
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_VAR)

    if condition:
        processor, composer, bytecode = variable_declaration(
            processor,
            composer,
            searcher,
            bytecode,
        )
    else:
        processor, composer, bytecode = statement(processor, composer, searcher, bytecode)

    if processor.panic_mode:
        processor = synchronize(processor, searcher)

    return processor, composer, bytecode


@expose
def statement(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, Compiler, chunk.Chunk]
    """Handler for statements."""
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_PRINT)

    if condition:
        processor, bytecode = print_statement(processor, composer, searcher, bytecode)
        return processor, composer, bytecode

    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_LEFT_BRACE)

    if condition:
        composer = begin_scope(processor, composer)
        processor, composer, bytecode = block(processor, composer, searcher, bytecode)
        return end_scope(processor, composer, bytecode)

    processor, bytecode = expression_statement(processor, composer, searcher, bytecode)
    return processor, composer, bytecode


@expose
def grouping(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Parser
    """Compiles expression between parentheses and consumes parentheses."""
    processor, bytecode = expression(processor, composer, searcher, bytecode)

    return consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_RIGHT_PAREN,
        "Expect ')' after expression.",
    )


@expose
def number(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Append number literal to bytecode."""
    assert processor.previous is not None
    assert processor.previous.source is not None
    val = float(processor.previous.source)

    return emit_constant(processor, searcher, bytecode, val)


@expose
def named_variable(processor, composer, searcher, bytecode, token):
    #
    """ Set local variable."""
    processor, arg = resolve_local(processor, composer, searcher, token)
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_EQUAL)

    if condition:
        processor, bytecode = expression(processor, composer, searcher, bytecode)
        return emit_bytes(processor, bytecode, chunk.OpCode.OP_SET_LOCAL, arg)

    return emit_bytes(processor, bytecode, chunk.OpCode.OP_GET_LOCAL, arg)


@expose
def variable(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Append variable to bytecode."""
    return named_variable(processor, composer, searcher, bytecode, processor.previous)


@expose
def unary(processor, composer, searcher, bytecode):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk) -> Tuple[Parser, chunk.Chunk]
    """Consumes leading minus and appends negated value."""
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the operand
    processor, bytecode = parse_precedence(
        processor,
        composer,
        searcher,
        bytecode,
        Precedence.PREC_UNARY,
    )

    # Emit the operator instruction
    if operator_type == scanner.TokenType.TOKEN_MINUS:
        processor, bytecode = emit_byte(processor, bytecode, chunk.OpCode.OP_NEGATE)

    return processor, bytecode


@expose
def parse_precedence(processor, composer, searcher, bytecode, precedence):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk, Precedence) -> Tuple[Parser, chunk.Chunk]
    """Starts at current token and parses expression at given precedence level
    or higher."""
    processor = advance(processor, searcher)

    assert processor.previous is not None
    prefix_rule = get_rule(processor.previous.token_type).prefix

    if prefix_rule is None:
        error(processor, searcher, "Expect expression")
        return processor, bytecode

    processor, bytecode = prefix_rule(processor, composer, searcher, bytecode)

    assert processor.current is not None
    while precedence.value <= get_rule(processor.current.token_type).precedence.value:
        processor = advance(processor, searcher)

        assert processor.previous is not None
        infix_rule = get_rule(processor.previous.token_type).infix

        assert infix_rule is not None
        processor, bytecode = infix_rule(processor, composer, searcher, bytecode)

    return processor, bytecode


def identifiers_equal(a, b):
    # type: (Optional[scanner.Token], Optional[scanner.Token]) -> bool
    """Checks if two tokens are equal."""
    if not a or not b or a.length != b.length:
        return False

    return a.source == b.source


@expose
def resolve_local(processor, composer, searcher, token):
    # type: (Parser, Compiler, scanner.Scanner, scanner.Token) -> Tuple[Parser, int]
    """Find last declared variable with given identifier."""
    for i in range(composer.local_count - 1, -1, -1):
        assert composer.locals is not None
        local = composer.locals[i]

        if identifiers_equal(token, local.token):
            if local.depth == -1:
                processor = error(
                    processor,
                    searcher,
                    "Cannot read local variable in its own initializer.",
                )

            return processor, i

    return processor, -1


@expose
def add_local(processor, composer, searcher, token):
    # type: (Parser, Compiler, scanner.Scanner, scanner.Token) -> Tuple[Parser, Compiler]
    """Include local variable to compiler's list in the current scope."""
    if composer.local_count == UINT8_COUNT:
        return error(processor, searcher, "Too many local variables in function."), composer

    assert composer.locals is not None
    local = composer.locals[composer.local_count]
    composer.local_count += 1

    local.token = token
    local.depth = composer.scope_depth

    return processor, composer


@expose
def declare_variable(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Record the existence of local variable in the compiler."""
    if composer.scope_depth == 0:
        return processor, composer

    token = processor.previous

    for i in range(composer.local_count - 1, -1, -1):
        assert composer.locals is not None
        local = composer.locals[i]

        if local.depth != -1 and local.depth < composer.scope_depth:
            break

        if identifiers_equal(token, local.token):
            processor = error(
                processor,
                searcher,
                "Variable with this name already declared in this scope.",
            )

            return processor, composer

    assert token is not None
    return add_local(processor, composer, searcher, token)


@expose
def parse_variable(processor, composer, searcher, bytecode, error_message):
    # type: (Parser, Compiler, scanner.Scanner, chunk.Chunk, str) -> Tuple[Parser, Optional[value.Value]]
    """Checks next token in local variable declaration is an identifier token."""
    processor = consume(processor, searcher, scanner.TokenType.TOKEN_IDENTIFIER, error_message)
    processor, composer = declare_variable(processor, composer, searcher)

    assert composer.scope_depth > 0
    return processor, 0


@expose
def mark_initialized(processor, composer):
    # type: (Parser, Compiler) -> Compiler
    """Mark local variable as initialized once variable set in compiler."""
    assert composer.scope_depth > 0
    local_count = composer.local_count - 1

    assert composer.locals is not None
    composer.locals[local_count].depth = composer.scope_depth

    return composer


@expose
def define_variable(processor, composer):
    # type: (Parser, Compiler) -> Compiler
    """Emit code to store local variable."""
    assert composer.scope_depth > 0
    return mark_initialized(processor, composer)


def get_rule(token_type):
    # type: (scanner.TokenType) -> ParseRule
    """Custom function to convert TokenType to ParseRule. This allows the
    rule_map to consist of strings, which are then replaced by respective
    classes in the conversion process."""
    type_map = {
        "binary": binary,
        "grouping": grouping,
        "number": number,
        "unary": unary,
        "variable": variable,
    }

    rule = rule_map[token_type.name]

    assert rule[2] is not None
    return ParseRule(
        prefix=None if rule[0] is None else type_map[rule[0]],
        infix=None if rule[1] is None else type_map[rule[1]],
        precedence=Precedence[rule[2]],
    )


def compile(source, bytecode, debug_level):
    # type: (scanner.Source, chunk.Chunk, int) -> Tuple[chunk.Chunk, bool]
    """Compiles source code into tokens."""
    searcher = scanner.init_scanner(source)
    processor = init_parser(debug_level)
    composer = init_compiler()

    if debug_level >= 2:
        print("\n== tokens ==")

    processor = advance(processor, searcher)

    while True:
        processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_EOF)

        if condition:
            break

        processor, _, bytecode = declaration(processor, composer, searcher, bytecode)

    processor, bytecode = end_compiler(processor, bytecode)

    if debug_level >= 1:
        debug.disassemble_chunk(bytecode, "script")

    return bytecode, not processor.had_error
