import re

from src.lexer.tokens import Token


KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
}

# This remains a lightweight regex lexer, not a complete Python lexer.
TOKEN_SPECIFICATION = [
    ("LINE_CONTINUATION", r"\\[ \t]*(?:\r\n|\r|\n)"),
    ("WHITESPACE", r"[ \t\f]+"),
    ("NEWLINE", r"\r\n|\r|\n"),
    ("COMMENT", r"\#[^\r\n]*"),
    (
        "STRING",
        r"(?i:[rubf]{0,2})(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:\\.|[^'\\\r\n])*'|\"(?:\\.|[^\"\\\r\n])*\")",
    ),
    (
        "NUMBER",
        r"(?:"
        r"0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*|"
        r"0[oO][0-7](?:_?[0-7])*|"
        r"0[bB][01](?:_?[01])*|"
        r"(?:[0-9](?:_?[0-9])*)?\.(?:[0-9](?:_?[0-9])*)?(?:[eE][+-]?[0-9](?:_?[0-9])*)?|"
        r"[0-9](?:_?[0-9])*(?:\.(?:[0-9](?:_?[0-9])*)?)?(?:[eE][+-]?[0-9](?:_?[0-9])*)?"
        r")[jJ]?",
    ),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    (
        "OPERATOR",
        r"\*\*=|//=|>>=|<<=|@=|:=|==|!=|<=|>=|"
        r"\+=|-=|\*=|/=|%=|&=|\|=|\^=|->|\*\*|//|<<|>>|"
        r"[+\-*/%@&|^~<>=]",
    ),
    ("PUNCTUATION", r"[()\[\]{},.:;]"),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION)
)


def _unicode_identifier_end(source: str, start: int) -> int:
    """Return the end of a Unicode identifier beginning at start, if any."""
    first = source[start]
    if not (first == "_" or first.isidentifier()):
        return start
    end = start + 1
    while end < len(source):
        char = source[end]
        # Appending to a valid identifier captures letters, digits, and marks.
        if (source[start:end] + char).isidentifier():
            end += 1
        elif char == "_" or ("a" + char).isidentifier():
            end += 1
        else:
            break
    return end


def lex(source: str, include_trivia: bool = False) -> list[Token]:
    """Tokenize a supported subset of Python source.

    Offsets are Python string character offsets [start, end). This lexer is
    intentionally lightweight; use lex_python_reference for Python's official
    tokenize-based reference behavior.
    """
    tokens = []
    position = 0
    line = 1
    column = 1

    while position < len(source):
        character = source[position]
        match = None

        # Scan identifiers manually so an ASCII prefix followed by Unicode
        # letters (for example, `café`) remains one identifier.
        if character == "_" or character.isidentifier():
            end = _unicode_identifier_end(source, position)
            value = source[position:end]
            token_type = "IDENTIFIER"
        elif character == "." and (
            position + 1 >= len(source)
            or not source[position + 1].isdigit()
        ):
            token_type = "PUNCTUATION"
            value = "."
            end = position + 1
        else:
            match = MASTER_PATTERN.match(source, position)
            if match is None:
                raise SyntaxError(
                    f"Unsupported character {character!r} "
                    f"at line {line}, column {column}"
                )
            token_type = match.lastgroup
            value = match.group()
            end = match.end()
            token_type = match.lastgroup
            value = match.group()
            end = match.end()

        start = position

        if token_type == "LINE_CONTINUATION":
            if include_trivia:
                tokens.append(Token("WHITESPACE", value, start, end, line, column))
            normalized = value.replace("\r\n", "\n").replace("\r", "\n")
            if "\n" in normalized:
                line += normalized.count("\n")
                column = len(normalized.rsplit("\n", 1)[-1]) + 1
            else:
                column += len(value)
            position = end
            continue

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
        normalized = value.replace("\r\n", "\n").replace("\r", "\n")
        if token_type == "NEWLINE":
            line += 1
            column = 1
        elif "\n" in normalized:
            line += normalized.count("\n")
            column = len(normalized.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(value)

    return tokens

