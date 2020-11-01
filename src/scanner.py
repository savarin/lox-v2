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
    TOKEN_EQUAL = "TOKEN_EQUAL"
    TOKEN_EQUAL_EQUAL = "TOKEN_EQUAL_EQUAL"

    # Literals
    TOKEN_IDENTIFIER = "TOKEN_IDENTIFIER"
    TOKEN_NUMBER = "TOKEN_NUMBER"

    # Keywords
    TOKEN_FUN = "TOKEN_FUN"
    TOKEN_LET = "TOKEN_LET"
    TOKEN_PRINT = "TOKEN_PRINT"
    TOKEN_RETURN = "TOKEN_RETURN"
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
    "=": (TokenType.TOKEN_EQUAL_EQUAL, TokenType.TOKEN_EQUAL),
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
    searcher = Scanner()
    searcher.source = source
    searcher.line = 1

    return searcher


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


def is_at_end(searcher):
    # type: (Scanner) -> bool
    """Checks if scanner at the end of the source code."""
    assert searcher.source is not None
    return searcher.current == len(searcher.source)


def advance(searcher):
    # type: (Scanner) -> Tuple[Scanner, Character]
    """Consumes and returns current character."""
    searcher.current += 1

    assert searcher.source is not None
    return searcher, searcher.source[searcher.current - 1]


def peek(searcher):
    # type: (Scanner) -> Character
    """Returns the current character without consuming it."""
    assert searcher.source is not None
    return searcher.source[searcher.current]


def peek_next(searcher):
    # type: (Scanner) -> Character
    """Returns the character past the current character without consuming it."""
    assert searcher.source is not None
    return searcher.source[searcher.current + 1]


def match(searcher, expected):
    # type: (Scanner, Character) -> Tuple[Scanner, bool]
    """Checks if current character is the desired character."""
    assert searcher.source is not None
    if is_at_end(searcher) or searcher.source[searcher.current] != expected:
        return searcher, False

    searcher.current += 1
    return searcher, True


def make_token(searcher, token_type):
    # type: (Scanner, TokenType) -> Token
    """Constructor-like function to create tokens."""
    assert searcher.source is not None
    return Token(
        token_type=token_type,
        start=searcher.start,
        length=searcher.current - searcher.start,
        source=searcher.source[searcher.start:searcher.current],
        line=searcher.line,
    )


def error_token(searcher, message):
    # type: (Scanner, str) -> Token
    """Returns error tokens with error message."""
    return Token(
        token_type=TokenType.TOKEN_ERROR,
        start=0,
        length=len(message),
        source=None,
        line=searcher.line,
    )


def skip_whitespace(searcher):
    # type: (Scanner) -> Scanner
    """Consumes every whitespace characters encountered."""
    while True:
        # Check since not using EOF marker
        if is_at_end(searcher):
            return searcher

        character = peek(searcher)

        if character in [" ", "\r", "\t"]:
            searcher, _ = advance(searcher)
            continue

        elif character == "\n":
            searcher.line += 1
            searcher, _ = advance(searcher)
            continue

        elif character == "/":
            if peek_next(searcher) == "/":
                while peek(searcher) != "\n" and not is_at_end(searcher):
                    searcher, _ = advance(searcher)
                continue
            else:
                return searcher

        return searcher


def check_keyword(searcher, start, length, rest, token_type):
    # type: (Scanner, int, int, str, TokenType) -> TokenType
    """Utility function to check full keyword matches."""
    index_start = searcher.start + start
    index_end = index_start + length

    assert searcher.source is not None
    is_correct_length = searcher.current - searcher.start == start + length
    is_actual_match = searcher.source[index_start:index_end] == rest

    if is_correct_length and is_actual_match:
        return token_type

    return TokenType.TOKEN_IDENTIFIER


def identifier_type(searcher):
    # type: (Scanner) -> TokenType
    """Checks identifier keywords and returns identifier token type."""
    assert searcher.source is not None
    character = searcher.source[searcher.start]

    if character == "f":
        return check_keyword(searcher, 1, 2, "un", TokenType.TOKEN_FUN)
    elif character == "l":
        return check_keyword(searcher, 1, 2, "et", TokenType.TOKEN_LET)
    elif character == "p":
        return check_keyword(searcher, 1, 4, "rint", TokenType.TOKEN_PRINT)
    elif character == "r":
        return check_keyword(searcher, 1, 5, "eturn", TokenType.TOKEN_RETURN)

    return TokenType.TOKEN_IDENTIFIER


def identifier(searcher):
    # type: (Scanner) -> Token
    """Converts identifier into token."""
    while is_alpha(peek(searcher)) or is_digit(peek(searcher)):
        searcher, _ = advance(searcher)

    return make_token(searcher, identifier_type(searcher))


def number(searcher):
    # type: (Scanner) -> Token
    """Convert number into token."""
    while is_digit(peek(searcher)):
        searcher, _ = advance(searcher)

    # Look for a fractional part
    if peek(searcher) == "." and is_digit(peek_next(searcher)):
        # Consume the period
        searcher, _ = advance(searcher)

        while is_digit(peek(searcher)):
            searcher, _ = advance(searcher)

    return make_token(searcher, TokenType.TOKEN_NUMBER)


def scan_token(searcher):
    # type: (Scanner) -> Token
    """Parses through source code and converts into tokens."""
    searcher = skip_whitespace(searcher)
    searcher.start = searcher.current

    if is_at_end(searcher):
        return make_token(searcher, TokenType.TOKEN_EOF)

    searcher, character = advance(searcher)

    if is_alpha(character):
        return identifier(searcher)

    if is_digit(character):
        return number(searcher)

    if character in single_token_map:
        return make_token(searcher, single_token_map[character])

    elif character in double_token_map:
        searcher, condition = match(searcher, "=")

        if condition:
            return make_token(searcher, double_token_map[character][0])
        else:
            return make_token(searcher, double_token_map[character][1])

    return error_token(searcher, "Unexpected character.")
