import enum
import functools
from typing import Callable, Dict, List, Optional, Tuple

import chunk
import debug
import function
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
    def __init__(self, token, depth):
        # type: (Optional[scanner.Token], int) -> None
        """Stores token and state of lexical scope."""
        self.token = token
        self.depth = depth


class Compiler():
    def __init__(self, composer):
        # type: (Optional[Compiler]) -> None
        """Stores local variables, count and scope depth."""
        self.enclosing = composer
        self.fun = None  # type: Optional[function.Function]
        self.locals = None  # type: Optional[List[Local]]
        self.local_count = 0
        self.scope_depth = 0


def init_compiler(composer=None):
    # type: (Optional[Compiler]) -> Compiler
    """Initialize new compiler."""
    composer = Compiler(composer)
    composer.fun = function.init_function(function.FunctionType.TYPE_SCRIPT)
    composer.locals = [Local(None, 0) for _ in range(UINT8_COUNT)]

    token = scanner.Token(scanner.TokenType.TOKEN_NIL, 0, 0, None, 0)
    local = Local(token, 0)
    composer.locals[composer.local_count] = local
    composer.local_count += 1

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

    processor = error_at_current(processor, searcher, message)

    return processor


@expose
def check(processor, token_type):
    # type: (Parser, scanner.TokenType) -> bool
    """Checks current_token has given type."""
    assert processor.current is not None
    return processor.current.token_type == token_type


@expose
def match(processor, searcher, token_type):
    # type: (Parser, scanner.Scanner, scanner.TokenType) -> Tuple[Parser, bool]
    """If current token has given type, consume token and return True."""
    if not check(processor, token_type):
        return processor, False

    return advance(processor, searcher), True


@expose
def emit_byte(processor, composer, byte):
    # type: (Parser, Compiler, chunk.Byte) -> Tuple[Parser, Compiler]
    """Append single byte to bytecode."""
    assert composer.fun is not None
    assert composer.fun.bytecode is not None
    assert processor.previous is not None
    composer.fun.bytecode = chunk.write_chunk(composer.fun.bytecode, byte, processor.previous.line)

    return processor, composer


@expose
def emit_bytes(processor, composer, byte1, byte2):
    # type: (Parser, Compiler, chunk.Byte, chunk.Byte) -> Tuple[Parser, Compiler]
    """Append two bytes to bytecode."""
    processor, composer = emit_byte(processor, composer, byte1)
    return emit_byte(processor, composer, byte2)


@expose
def emit_return(processor, composer):
    # type: (Parser, Compiler) -> Tuple[Parser, Compiler]
    """Clean up after complete compilation stage."""
    return emit_byte(processor, composer, chunk.OpCode.OP_RETURN)


@expose
def make_constant(processor, composer, searcher, val):
    # type: (Parser, Compiler, scanner.Scanner, value.Value) -> Tuple[Parser, Compiler, Optional[value.Value]]
    """Add value to constant table."""
    assert composer.fun is not None
    assert composer.fun.bytecode is not None
    composer.fun.bytecode, constant = chunk.add_constant(composer.fun.bytecode, val)

    if constant > UINT8_MAX:
        processor = error(processor, searcher, "Too many constants in one chunk.")
        return processor, composer, None

    return processor, composer, constant


@expose
def emit_constant(processor, composer, searcher, val):
    # type: (Parser, Compiler, scanner.Scanner, value.Value) -> Tuple[Parser, Compiler]
    """Append constant to bytecode."""
    processor, composer, constant = make_constant(processor, composer, searcher, val)

    assert constant is not None
    return emit_bytes(processor, composer, chunk.OpCode.OP_CONSTANT, constant)


@expose
def end_compiler(processor, composer):
    # type: (Parser, Compiler) -> Tuple[Parser, Optional[Compiler], function.Function]
    """Implement end of expression."""
    processor, composer = emit_return(processor, composer)

    assert composer is not None
    fun = composer.fun
    enclosing = composer.enclosing

    assert fun is not None
    return processor, enclosing, fun


@expose
def begin_scope(processor, composer):
    # type: (Parser, Compiler) -> Compiler
    """Enter a new local scope."""
    composer.scope_depth += 1
    return composer


@expose
def end_scope(processor, composer):
    # type: (Parser, Compiler) -> Tuple[Parser, Compiler]
    """Exit local scope."""
    composer.scope_depth -= 1

    while True:
        is_positive = composer.local_count > 0

        assert composer.locals is not None
        depth = composer.locals[composer.local_count - 1].depth
        is_over_scope = depth > composer.scope_depth

        if not is_positive or not is_over_scope:
            break

        processor, composer = emit_byte(processor, composer, chunk.OpCode.OP_POP)
        composer.local_count -= 1

    return processor, composer


@expose
def binary(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Implements infix parser for binary operations."""
    # Remember the operator
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the right operand.
    rule = get_rule(operator_type)

    # Get precedence which has 1 priority level above precedence of current rule
    precedence = Precedence(rule.precedence.value + 1)
    processor, composer = parse_precedence(processor, composer, searcher, precedence)

    if operator_type == scanner.TokenType.TOKEN_PLUS:
        return emit_byte(processor, composer, chunk.OpCode.OP_ADD)
    elif operator_type == scanner.TokenType.TOKEN_MINUS:
        return emit_byte(processor, composer, chunk.OpCode.OP_SUBTRACT)
    elif operator_type == scanner.TokenType.TOKEN_STAR:
        return emit_byte(processor, composer, chunk.OpCode.OP_MULTIPLY)
    elif operator_type == scanner.TokenType.TOKEN_SLASH:
        return emit_byte(processor, composer, chunk.OpCode.OP_DIVIDE)

    return processor, composer


@expose
def expression(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Compiles expression."""
    return parse_precedence(processor, composer, searcher, Precedence.PREC_ASSIGNMENT)


@expose
def block(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Compile block within scope."""
    while True:
        is_right_brace = check(processor, scanner.TokenType.TOKEN_RIGHT_BRACE)
        is_eof = check(processor, scanner.TokenType.TOKEN_EOF)

        if is_right_brace or is_eof:
            break

        processor, composer = declaration(processor, composer, searcher)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_RIGHT_BRACE,
        "Expect '}' after block.",
    )

    return processor, composer


def define_function(processor, composer, searcher, function_type):
    # type: (Parser, Compiler, scanner.Scanner, function.FunctionType) -> Tuple[Parser, Compiler]
    """
    """
    composer = init_compiler(composer)
    composer = begin_scope(processor, composer)

    # Compile the parameter list
    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_LEFT_PAREN,
        "Expect '(' after function name.",
    )

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_RIGHT_PAREN,
        "Expect ')' after parameters.",
    )

    # The body
    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_LEFT_BRACE,
        "Expect '{' before function body.",
    )

    processor, composer = block(processor, composer, searcher)

    # Create the function object
    processor, composer, fun = end_compiler(processor, composer)
    processor, composer, constant = make_constant(processor, composer, searcher, fun)

    return emit_bytes(processor, composer, chunk.OpCode.OP_CONSTANT, constant)


@expose
def function_declaration(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """
    """
    processor, composer = parse_variable(processor, composer, searcher, "Expect function name.")
    composer = mark_initialized(processor, composer)

    processor, composer = define_function(
        processor,
        composer,
        searcher,
        function.FunctionType.TYPE_FUNCTION,
    )

    composer = define_variable(processor, composer)

    return processor, composer


@expose
def variable_declaration(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Declare variable when corresponding token matched."""
    processor, composer = parse_variable(processor, composer, searcher, "Expect variable name.")
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_EQUAL)

    assert condition
    processor, composer = expression(processor, composer, searcher)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after variable declaration.",
    )

    composer = define_variable(processor, composer)

    return processor, composer


@expose
def expression_statement(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Evaluates expression statement prior to semicolon."""
    processor, composer = expression(processor, composer, searcher)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, composer, chunk.OpCode.OP_POP)


@expose
def print_statement(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Evaluates expression and prints result."""
    processor, composer = expression(processor, composer, searcher)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_SEMICOLON,
        "Expect ';' after expression.",
    )

    return emit_byte(processor, composer, chunk.OpCode.OP_PRINT)


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
def declaration(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Compiles declarations until end of source code reached."""
    def wrapper(processor, composer, searcher):
        #
        if processor.panic_mode:
            processor = synchronize(processor, searcher)
        return processor, composer

    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_FUN)

    if condition:
        processor, composer = function_declaration(processor, composer, searcher)
        return wrapper(processor, composer, searcher)

    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_VAR)

    if condition:
        processor, composer = variable_declaration(processor, composer, searcher)
        return wrapper(processor, composer, searcher)

    processor, composer = statement(processor, composer, searcher)
    return wrapper(processor, composer, searcher)


@expose
def statement(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Handler for statements."""
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_PRINT)

    if condition:
        processor, composer = print_statement(processor, composer, searcher)
        return processor, composer

    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_LEFT_BRACE)

    if condition:
        composer = begin_scope(processor, composer)
        processor, composer = block(processor, composer, searcher)
        return end_scope(processor, composer)

    processor, composer = expression_statement(processor, composer, searcher)
    return processor, composer


@expose
def grouping(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Compiles expression between parentheses and consumes parentheses."""
    processor, composer = expression(processor, composer, searcher)

    processor = consume(
        processor,
        searcher,
        scanner.TokenType.TOKEN_RIGHT_PAREN,
        "Expect ')' after expression.",
    )

    return processor, composer


@expose
def number(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Append number literal to bytecode."""
    assert processor.previous is not None
    assert processor.previous.source is not None
    val = float(processor.previous.source)

    return emit_constant(processor, composer, searcher, val)


@expose
def named_variable(processor, composer, searcher, token):
    # type: (Parser, Compiler, scanner.Scanner, scanner.Token) -> Tuple[Parser, Compiler]
    """ Set local variable."""
    processor, arg = resolve_local(processor, composer, searcher, token)
    processor, condition = match(processor, searcher, scanner.TokenType.TOKEN_EQUAL)

    if condition:
        processor, composer = expression(processor, composer, searcher)
        return emit_bytes(processor, composer, chunk.OpCode.OP_SET_LOCAL, arg)

    return emit_bytes(processor, composer, chunk.OpCode.OP_GET_LOCAL, arg)


@expose
def variable(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Append variable to bytecode."""
    return named_variable(processor, composer, searcher, processor.previous)


@expose
def unary(processor, composer, searcher):
    # type: (Parser, Compiler, scanner.Scanner) -> Tuple[Parser, Compiler]
    """Consumes leading minus and appends negated value."""
    assert processor.previous is not None
    operator_type = processor.previous.token_type

    # Compile the operand
    processor, composer = parse_precedence(processor, composer, searcher, Precedence.PREC_UNARY)

    # Emit the operator instruction
    if operator_type == scanner.TokenType.TOKEN_MINUS:
        processor, composer = emit_byte(processor, composer, chunk.OpCode.OP_NEGATE)

    return processor, composer


@expose
def parse_precedence(processor, composer, searcher, precedence):
    # type: (Parser, Compiler, scanner.Scanner, Precedence) -> Tuple[Parser, Compiler]
    """Starts at current token and parses expression at given precedence level
    or higher."""
    processor = advance(processor, searcher)

    assert processor.previous is not None
    prefix_rule = get_rule(processor.previous.token_type).prefix

    if prefix_rule is None:
        processor = error(processor, searcher, "Expect expression")
        return processor, composer

    processor, composer = prefix_rule(processor, composer, searcher)

    assert processor.current is not None
    while precedence.value <= get_rule(processor.current.token_type).precedence.value:
        processor = advance(processor, searcher)

        assert processor.previous is not None
        infix_rule = get_rule(processor.previous.token_type).infix

        assert infix_rule is not None
        processor, composer = infix_rule(processor, composer, searcher)

    return processor, composer


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
    composer.locals[composer.local_count] = Local(token, composer.scope_depth)
    composer.local_count += 1

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
def parse_variable(processor, composer, searcher, error_message):
    # type: (Parser, Compiler, scanner.Scanner, str) -> Tuple[Parser, Compiler]
    """Checks next token in local variable declaration is an identifier token."""
    processor = consume(processor, searcher, scanner.TokenType.TOKEN_IDENTIFIER, error_message)
    processor, composer = declare_variable(processor, composer, searcher)

    assert composer.scope_depth > 0
    return processor, composer


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


def compile(source, debug_level):
    # type: (scanner.Source, int) -> Optional[function.Function]
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

        processor, composer = declaration(processor, composer, searcher)

    processor, composer, fun = end_compiler(processor, composer)
    assert composer is None

    if processor.debug_level >= 1:
        debug.disassemble_chunk(fun.bytecode, "script")

    if processor.had_error:
        function.free_function(fun, function.FunctionType.TYPE_SCRIPT)
        return None

    return fun
