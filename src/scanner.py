import enum
from typing import Optional, Tuple

Source = str
Character = str


class TokenType(enum.Enum):
    # Single-character tokens
    TOKEN_LEFT_PAREN = "TOKEN_LEFT_PAREN"
    TOKEN_RIGHT_PAREN = "TOKEN_RIGHT_PAREN"
    TOKEN_LEFT_BRACE = "TOKEN_LEFT_BRACE"
    TOKEN_RIGHT_BRACE = "TOKEN_RIGHT_BRACE"
    TOKEN_MINUS = "TOKEN_MINUS"
    TOKEN_PLUS = "TOKEN_PLUS"
    TOKEN_SEMICOLON = "TOKEN_SEMICOLON"
    TOKEN_SLASH = "TOKEN_SLASH"
    TOKEN_STAR = "TOKEN_STAR"

    # One or two character tokens
    TOKEN_BANG = "TOKEN_BANG"
    TOKEN_BANG_EQUAL = "TOKEN_BANG_EQUAL"
    TOKEN_EQUAL = "TOKEN_EQUAL"
    TOKEN_EQUAL_EQUAL = "TOKEN_EQUAL_EQUAL"
    TOKEN_GREATER = "TOKEN_GREATER"
    TOKEN_GREATER_EQUAL = "TOKEN_GREATER_EQUAL"
    TOKEN_LESS = "TOKEN_LESS"
    TOKEN_LESS_EQUAL = "TOKEN_LESS_EQUAL"

    # Literals
    TOKEN_IDENTIFIER = "TOKEN_IDENTIFIER"
    TOKEN_STRING = "TOKEN_STRING"
    TOKEN_NUMBER = "TOKEN_NUMBER"

    # Keywords
    TOKEN_FALSE = "TOKEN_FALSE"
    TOKEN_FUN = "TOKEN_FUN"
    TOKEN_PRINT = "TOKEN_PRINT"
    TOKEN_RETURN = "TOKEN_RETURN"
    TOKEN_TRUE = "TOKEN_TRUE"
    TOKEN_VAR = "TOKEN_VAR"
    TOKEN_ERROR = "TOKEN_ERROR"
    TOKEN_EOF = "TOKEN_EOF"


class Token():
    def __init__(self, token_type, start, length, source, line):
        # type: (TokenType, int, int, Optional[str], int) -> None
        """Stores details of tokens converted from source code."""
        self.token_type = token_type
        self.start = start
        self.length = length
        self.source = source
        self.line = line


single_token_map = {
    "(": TokenType.TOKEN_LEFT_PAREN,
    ")": TokenType.TOKEN_RIGHT_PAREN,
    "{": TokenType.TOKEN_LEFT_BRACE,
    "}": TokenType.TOKEN_RIGHT_BRACE,
    ";": TokenType.TOKEN_SEMICOLON,
    "-": TokenType.TOKEN_MINUS,
    "+": TokenType.TOKEN_PLUS,
    "/": TokenType.TOKEN_SLASH,
    "*": TokenType.TOKEN_STAR,
}

double_token_map = {
    "!": (TokenType.TOKEN_BANG_EQUAL, TokenType.TOKEN_BANG),
    "=": (TokenType.TOKEN_EQUAL_EQUAL, TokenType.TOKEN_EQUAL),
    "<": (TokenType.TOKEN_LESS_EQUAL, TokenType.TOKEN_LESS),
    ">": (TokenType.TOKEN_GREATER_EQUAL, TokenType.TOKEN_GREATER),
}


class Scanner():
    def __init__(self):
        # type: () -> None
        """Stores details pertaining to source code."""
        self.start = 0
        self.current = 0
        self.source = None  # type: Optional[Source]
        self.line = 0


def init_scanner(source):
    # type: (Source) -> Scanner
    """Initialize new scanner."""
    reader = Scanner()

    reader.source = source
    reader.line = 1

    return reader


def is_alpha(character):
    # type: (Character) -> bool
    """Checks if character is an alphabet."""
    is_lowercase = character >= "a" and character <= "z"
    is_uppercase = character >= "A" and character <= "Z"
    is_underscore = character == "_"

    return is_lowercase or is_uppercase or is_underscore


def is_digit(character):
    # type: (Character) -> bool
    """Checks if character is a digit."""
    return character >= "0" and character <= "9"


def is_at_end(reader):
    # type: (Scanner) -> bool
    """Checks if scanner at the end of the source code."""
    assert reader.source is not None
    return reader.current == len(reader.source)


def advance(reader):
    # type: (Scanner) -> Tuple[Scanner, Character]
    """Consumes and returns current character."""
    reader.current += 1

    assert reader.source is not None
    return reader, reader.source[reader.current - 1]


def peek(reader):
    # type: (Scanner) -> Character
    """Returns the current character without consuming it."""
    assert reader.source is not None
    return reader.source[reader.current]


def peek_next(reader):
    # type: (Scanner) -> Character
    """Returns the character past the current character without consuming it."""
    assert reader.source is not None
    return reader.source[reader.current + 1]


def match(reader, expected):
    # type: (Scanner, Character) -> Tuple[Scanner, bool]
    """Checks if current character is the desired character."""
    assert reader.source is not None

    if is_at_end(reader):
        return reader, False

    elif reader.source[reader.current] != expected:
        return reader, False

    reader.current += 1
    return reader, True


def make_token(reader, token_type):
    # type: (Scanner, TokenType) -> Token
    """Constructor-like function to create tokens."""
    assert reader.source is not None
    return Token(
        token_type=token_type,
        start=reader.start,
        length=reader.current - reader.start,
        source=reader.source[reader.start:reader.current],
        line=reader.line,
    )


def error_token(reader, message):
    # type: (Scanner, str) -> Token
    """Returns error tokens with error message."""
    return Token(
        token_type=TokenType.TOKEN_ERROR,
        start=0,
        length=len(message),
        source=None,
        line=reader.line,
    )


def skip_whitespace(reader):
    # type: (Scanner) -> Scanner
    """Consumes every whitespace characters encountered."""
    while True:
        character = peek(reader)

        if character in [" ", "\r", "\t"]:
            reader, _ = advance(reader)
            continue

        elif character == "\n":
            reader.line += 1
            reader, character = advance(reader)
            continue

        elif character == "/":
            if peek_next(reader) == "/":
                while peek(reader) != "\n" and not is_at_end(reader):
                    reader, _ = advance(reader)
                continue
            else:
                return reader

        return reader


def check_keyword(reader, start, length, rest, token_type):
    # type: (Scanner, int, int, str, TokenType) -> TokenType
    """Utility function to check full keyword matches."""
    index_start = reader.start + start
    index_end = index_start + length

    assert reader.source is not None
    is_correct_length = reader.current - reader.start == start + length
    is_actual_match = reader.source[index_start:index_end] == rest

    if is_correct_length and is_actual_match:
        return token_type

    return TokenType.TOKEN_IDENTIFIER


def identifier_type(reader):
    # type: (Scanner) -> TokenType
    """Checks identifier keywords and returns identifier token type."""
    assert reader.source is not None
    character = reader.source[reader.start]

    if character == "l":
        return check_keyword(reader, 1, 2, "et", TokenType.TOKEN_VAR)
    elif character == "p":
        return check_keyword(reader, 1, 4, "rint", TokenType.TOKEN_PRINT)
    elif character == "r":
        return check_keyword(reader, 1, 5, "eturn", TokenType.TOKEN_RETURN)
    elif character == "t":
        return check_keyword(reader, 1, 3, "rue", TokenType.TOKEN_TRUE)
    elif character == "f":
        if reader.current - reader.start > 1:
            next_character = reader.source[reader.start + 1]
            if next_character == "a":
                return check_keyword(reader, 2, 3, "lse", TokenType.TOKEN_FALSE)
            if next_character == "u":
                return check_keyword(reader, 2, 1, "n", TokenType.TOKEN_FUN)

    return TokenType.TOKEN_IDENTIFIER


def identifier(reader):
    # type: (Scanner) -> Token
    """Converts identifier into token."""
    while is_alpha(peek(reader)) or is_digit(peek(reader)):
        reader, _ = advance(reader)

    return make_token(reader, identifier_type(reader))


def number(reader):
    # type: (Scanner) -> Token
    """Convert number into token."""
    while is_digit(peek(reader)):
        reader, _ = advance(reader)

    # Look for a fractional part
    if peek(reader) == "." and is_digit(peek_next(reader)):
        # Consume the period
        reader, _ = advance(reader)

        while is_digit(peek(reader)):
            reader, _ = advance(reader)

    return make_token(reader, TokenType.TOKEN_NUMBER)


def string(reader):
    # type: (Scanner) -> Token
    """Convert string into token."""
    while peek(reader) != '"' and not is_at_end(reader):
        if peek(reader) == "\n":
            reader.line += 1
        reader, _ = advance(reader)

    if is_at_end(reader):
        return error_token(reader, "Unterminated string.")

    reader, _ = advance(reader)
    return make_token(reader, TokenType.TOKEN_STRING)


def scan_token(reader):
    # type: (Scanner) -> Token
    """Parses through source code and converts into tokens."""
    reader = skip_whitespace(reader)
    reader.start = reader.current

    if is_at_end(reader):
        return make_token(reader, TokenType.TOKEN_EOF)

    reader, character = advance(reader)

    if is_alpha(character):
        return identifier(reader)

    if is_digit(character):
        return number(reader)

    if character in single_token_map:
        return make_token(reader, single_token_map[character])

    elif character in double_token_map:
        reader, condition = match(reader, "=")

        if condition:
            return make_token(reader, double_token_map[character][0])
        else:
            return make_token(reader, double_token_map[character][1])

    elif character == '"':
        return string(reader)

    return error_token(reader, "Unexpected character.")
