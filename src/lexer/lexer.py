import re

from src.lexer.tokens import Token


KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
}

# This is intentionally a lightweight lexer for a subset of Python.
# It is not a replacement for Python's complete lexical specification.
TOKEN_SPECIFICATION = [
    ("WHITESPACE", r"[ \t\f]+"),
    ("NEWLINE", r"\r\n|\r|\n"),
    ("COMMENT", r"\#[^\r\n]*"),
    (
        "STRING",
        r"""(?i:[rubf]{0,2})(?:'(?:\\.|[^'\\\r\n])*'|"(?:\\.|[^"\\\r\n])*")""",
    ),
    ("FLOAT", r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?"),
    ("INTEGER", r"\d+"),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    (
        "OPERATOR",
        r"\*\*=|//=|>>=|<<=|:=|==|!=|<=|>=|"
        r"\+=|-=|\*=|/=|%=|&=|\|=|\^=|"
        r"->|\*\*|//|<<|>>|"
        r"[+\-*/%@&|^~<>=]",
    ),
    ("PUNCTUATION", r"[()\[\]{},.:;]"),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION)
)


def lex(source: str, include_trivia: bool = False) -> list[Token]:
    """
    Tokenize the supported subset of Python source.

    Offsets are Python string character offsets [start, end).
    WHITESPACE and COMMENT are omitted unless include_trivia=True.
    NEWLINE tokens are retained.
    """
    tokens = []
    position = 0
    line = 1
    column = 1

    while position < len(source):
        match = MASTER_PATTERN.match(source, position)
        if match is None:
            character = source[position]
            raise SyntaxError(
                f"Unsupported character {character!r} at line {line}, column {column}"
            )

        token_type = match.lastgroup
        value = match.group()
        start, end = position, match.end()

        if token_type == "IDENTIFIER" and value in KEYWORDS:
            token_type = "KEYWORD"

        token = Token(
            token_type=token_type,
            value=value,
            start=start,
            end=end,
            line=line,
            column=column,
        )

        if include_trivia or token_type not in {"WHITESPACE", "COMMENT"}:
            tokens.append(token)

        position = end
        if token_type == "NEWLINE":
            line += 1
            column = 1
        else:
            column += len(value)

    return tokens
