import io
import tokenize

from src.lexer.tokens import Token


TRIVIA_TYPES = {"WHITESPACE", "COMMENT", "NL", "NEWLINE", "INDENT", "DEDENT"}


def lex_python_reference(source: str, include_trivia: bool = False) -> list[Token]:
    """
    Tokenize Python source using Python's standard tokenize module.

    Token offsets use Python string character positions [start, end).
    """
    tokens = []

    reference_tokens = tokenize.generate_tokens(
        io.StringIO(source).readline
    )
    lines = source.splitlines(keepends=True)
    line_offsets = [0]
    for part in lines:
        line_offsets.append(line_offsets[-1] + len(part))

    def absolute_offset(line, column):
        return line_offsets[line - 1] + column

    for item in reference_tokens:
        token_type = tokenize.tok_name[item.type]
        value = item.string

        if token_type in {"ENCODING", "ENDMARKER"}:
            continue

        # Convert line/column positions into absolute character offsets.
        start_line, start_column = item.start
        end_line, end_column = item.end

        start = absolute_offset(start_line, start_column)
        end = absolute_offset(end_line, end_column)

        if token_type == "NAME":
            normalized_type = "KEYWORD" if value in {
                "False", "None", "True", "and", "as", "assert", "async",
                "await", "break", "class", "continue", "def", "del",
                "elif", "else", "except", "finally", "for", "from",
                "global", "if", "import", "in", "is", "lambda",
                "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield",
            } else "IDENTIFIER"
        elif token_type == "OP":
            normalized_type = (
                "PUNCTUATION" if value in "()[]{}.,:;"
                else "OPERATOR"
            )
        elif token_type == "NUMBER":
            normalized_type = "NUMBER"
        elif token_type == "STRING":
            normalized_type = "STRING"
        elif token_type in {"NL", "NEWLINE"}:
            normalized_type = "NEWLINE"
        elif token_type in {"INDENT", "DEDENT"}:
            normalized_type = token_type
        elif token_type == "COMMENT":
            normalized_type = "COMMENT"
        else:
            normalized_type = token_type

        if not include_trivia and normalized_type in TRIVIA_TYPES:
            continue

        tokens.append(
            Token(
                token_type=normalized_type,
                value=value,
                start=start,
                end=end,
                line=start_line,
                column=start_column + 1,
            )
        )

    return tokens
