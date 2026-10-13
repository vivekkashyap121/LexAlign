from collections import Counter

from src.lexer.lexer import lex as lex_custom
from src.lexer.python_reference import lex_python_reference


TRIVIA_TYPES = {"WHITESPACE", "NEWLINE", "NL", "COMMENT", "INDENT", "DEDENT"}


def build_alignment_profile(source, tokenizer, reference="custom"):
    """
    Compare tokenizer offsets with lexer token boundaries.

    Categories are based on overlap with meaningful lexer tokens.
    Whitespace and newlines are recorded separately through each
    tokenizer token's source span.
    """
    if reference == "custom":
        lexer_tokens = lex_custom(source, include_trivia=True)
    elif reference == "python":
        lexer_tokens = lex_python_reference(source, include_trivia=True)
    else:
        raise ValueError("reference must be either custom or python")

    meaningful_tokens = [
        token
        for token in lexer_tokens
        if token.token_type not in TRIVIA_TYPES
    ]

    encoded = tokenizer(
        source,
        add_special_tokens=False,
        return_offsets_mapping=True,
    )

    token_ids = encoded["input_ids"]
    offsets = encoded["offset_mapping"]
    token_strings = tokenizer.convert_ids_to_tokens(token_ids)

    counts = Counter()
    source_kind_counts = Counter()
    details = []

    for token_id, token_string, offset in zip(
        token_ids, token_strings, offsets
    ):
        start, end = offset
        source_text = source[start:end]

        if start == end:
            category = "ZERO_LENGTH"
        else:
            overlapping = [
                token for token in meaningful_tokens
                if token.start < end and start < token.end
            ]

            overlapping_all = [
                token for token in lexer_tokens
                if token.start < end and start < token.end
            ]

            has_whitespace = any(char.isspace() for char in source_text)
            has_code = any(
                token.token_type not in TRIVIA_TYPES
                for token in overlapping_all
            )

            if has_whitespace and has_code:
                category = "TRIVIA_MIXED"

            elif not overlapping:
                category = "UNCLASSIFIED"

            elif len(overlapping) > 1:
                category = "BOUNDARY_STRADDLING"

            else:
                lexeme = overlapping[0]

                if start == lexeme.start and end == lexeme.end:
                    category = "WHOLE_LEXEME"

                elif start < lexeme.start or end > lexeme.end:
                    category = "BOUNDARY_STRADDLING"

                else:
                    category = "SUB_LEXEME"

        overlapping_all = [
            token for token in lexer_tokens
            if token.start < end and start < token.end
        ] if start != end else []

        overlapping_meaningful = [
            token for token in meaningful_tokens
            if token.start < end and start < token.end
        ] if start != end else []

        has_whitespace = any(char.isspace() for char in source_text)
        has_code = any(not char.isspace() for char in source_text)
        has_comment = any(
            token.token_type == "COMMENT"
            for token in overlapping_all
        )

        if start == end:
            source_kind = "EMPTY"
        elif has_comment and has_whitespace:
            source_kind = "MIXED_TRIVIA_AND_CODE"
        elif has_comment:
            source_kind = "COMMENT"
        elif has_whitespace and has_code:
            source_kind = "MIXED_WHITESPACE_AND_CODE"
        elif has_whitespace:
            source_kind = "WHITESPACE_ONLY"
        else:
            source_kind = "NO_WHITESPACE"

        exact_boundary_match = (
            len(overlapping_meaningful) == 1
            and start == overlapping_meaningful[0].start
            and end == overlapping_meaningful[0].end
        )

        counts[category] += 1
        source_kind_counts[source_kind] += 1

        details.append({
            "token_id": token_id,
            "token": token_string,
            "start": start,
            "end": end,
            "source_text": source_text,
            "category": category,
            "source_kind": source_kind,
            "exact_boundary_match": exact_boundary_match,
            "overlapping_lexer_types": list(
                dict.fromkeys(
                    token.token_type for token in overlapping_all
                )
            ),
            "overlapping_lexemes": [
                token.value for token in overlapping_meaningful
            ],
        })

    total = len(token_ids)
    exact_count = sum(
        item["exact_boundary_match"] for item in details
    )

    return {
        "token_count": total,
        "counts": dict(counts),
        "source_kind_counts": dict(source_kind_counts),
        "exact_boundary_match_count": exact_count,
        "exact_boundary_match_ratio": (
            exact_count / total if total else 0.0
        ),
        "straddling_ratio": (
            counts["BOUNDARY_STRADDLING"] / total if total else 0.0
        ),
        "tokens": details,
    }
