import scanner


def compile(source):
    # type: scanner.Source -> None
    """Compiles source code into tokens."""
    reader = scanner.init_scanner(source)
    line = -1

    while True:
        token = reader.scan_token()

        if token.line != line:
            print("{:04d}".format(token.line), end=" ")
            line = token.line
        else:
            print("   |", end=" ")

        current_token = reader.source[token.start:(token.start + token.length)]
        print("{} '{}'".format(token.token_type, current_token))

        if token.token_type == scanner.TokenType.TOKEN_EOF:
            break
