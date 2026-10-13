import unittest

from src.alignment.profile import build_alignment_profile
from src.lexer.lexer import lex


class FakeTokenizer:
    """Tiny deterministic tokenizer stub for tests; no network required."""

    is_fast = True

    def __call__(
        self, source, add_special_tokens=False, return_offsets_mapping=False
    ):
        return {
            "input_ids": list(range(len(source))),
            "offset_mapping": [(i, i + 1) for i in range(len(source))],
        }

    def convert_ids_to_tokens(self, token_ids):
        return [str(token_id) for token_id in token_ids]


class LexerTests(unittest.TestCase):
    def test_identifier_and_operator(self):
        tokens = lex("total_marks = 95")
        self.assertEqual(
            [(token.token_type, token.value) for token in tokens],
            [
                ("IDENTIFIER", "total_marks"),
                ("OPERATOR", "="),
                ("INTEGER", "95"),
            ],
        )

    def test_trivia_inclusion(self):
        tokens = lex("x = 1 # comment\n", include_trivia=True)
        types = [token.token_type for token in tokens]
        self.assertIn("WHITESPACE", types)
        self.assertIn("COMMENT", types)
        self.assertIn("NEWLINE", types)


class AlignmentTests(unittest.TestCase):
    def test_profile_has_one_record_per_token(self):
        source = "x=1"
        profile = build_alignment_profile(source, FakeTokenizer())
        self.assertEqual(profile["token_count"], 3)
        self.assertEqual(len(profile["tokens"]), 3)

    def test_counts_sum_to_total(self):
        source = "x = 1\n"
        profile = build_alignment_profile(source, FakeTokenizer())
        self.assertEqual(
            sum(profile["counts"].values()),
            profile["token_count"],
        )

    def test_source_spans_match(self):
        source = "x=1"
        profile = build_alignment_profile(source, FakeTokenizer())
        for item in profile["tokens"]:
            self.assertEqual(
                item["source_text"],
                source[item["start"]:item["end"]],
            )

    def test_exact_boundary_matches_for_simple_expression(self):
        source = "x=1"
        profile = build_alignment_profile(source, FakeTokenizer())
        self.assertEqual(profile["exact_boundary_match_count"], 3)
        self.assertAlmostEqual(
            profile["exact_boundary_match_ratio"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()


class SplittingTokenizer:
    """Fake tokenizer that splits a Python identifier into pieces."""

    is_fast = True

    def __call__(
        self, source, add_special_tokens=False, return_offsets_mapping=False
    ):
        pieces = []
        offsets = []
        position = 0

        while position < len(source):
            if source.startswith("total_marks", position):
                pieces.extend([101, 102, 103])
                offsets.extend([
                    (position, position + 5),
                    (position + 5, position + 6),
                    (position + 6, position + 11),
                ])
                position += 11
            else:
                pieces.append(ord(source[position]))
                offsets.append((position, position + 1))
                position += 1

        return {
            "input_ids": pieces,
            "offset_mapping": offsets,
        }

    def convert_ids_to_tokens(self, token_ids):
        return [
            {101: "total", 102: "_", 103: "marks"}.get(
                token_id, chr(token_id) if token_id < 101 else str(token_id)
            )
            for token_id in token_ids
        ]


class IdentifierSplittingTests(unittest.TestCase):
    def test_identifier_is_split_into_sub_lexemes(self):
        source = "total_marks"
        profile = build_alignment_profile(source, SplittingTokenizer())

        identifier_tokens = [
            item for item in profile["tokens"]
            if item["start"] < len(source) and item["end"] > 0
        ]

        self.assertEqual(len(identifier_tokens), 3)
        self.assertTrue(
            all(item["category"] == "SUB_LEXEME"
                for item in identifier_tokens)
        )


class WhitespaceAndOperatorTokenizer:
    is_fast = True

    def __call__(
        self, source, add_special_tokens=False, return_offsets_mapping=False
    ):
        return {
            "input_ids": [1, 2, 3],
            "offset_mapping": [(0, 1), (1, 3), (4, 5)],
        }

    def convert_ids_to_tokens(self, token_ids):
        return ["x", "Ġ=", "1"]


class WhitespaceSpanTests(unittest.TestCase):
    def test_whitespace_plus_operator_is_not_whole_lexeme(self):
        source = "x = 1"
        profile = build_alignment_profile(
            source, WhitespaceAndOperatorTokenizer()
        )

        equals_token = next(
            item for item in profile["tokens"]
            if item["source_text"] == " ="
        )

        self.assertNotEqual(equals_token["category"], "WHOLE_LEXEME")
        self.assertFalse(equals_token["exact_boundary_match"])

class ClosingPunctuationTokenizer:
    """Fake tokenizer that combines ')' and ':' into one token."""

    is_fast = True

    def __call__(
        self, source, add_special_tokens=False, return_offsets_mapping=False
    ):
        pieces = []
        offsets = []
        position = 0

        while position < len(source):
            if source.startswith("):", position):
                pieces.append(999)
                offsets.append((position, position + 2))
                position += 2
            else:
                pieces.append(ord(source[position]))
                offsets.append((position, position + 1))
                position += 1

        return {
            "input_ids": pieces,
            "offset_mapping": offsets,
        }

    def convert_ids_to_tokens(self, token_ids):
        return [
            "):" if token_id == 999 else chr(token_id)
            for token_id in token_ids
        ]


class BoundaryStraddlingTests(unittest.TestCase):
    def test_combined_closing_punctuation_straddles_lexer_tokens(self):
        source = "def f():"
        profile = build_alignment_profile(
            source, ClosingPunctuationTokenizer()
        )

        combined_token = next(
            item for item in profile["tokens"]
            if item["source_text"] == "):"
        )

        self.assertEqual(
            combined_token["category"],
            "BOUNDARY_STRADDLING",
        )
        self.assertFalse(combined_token["exact_boundary_match"])

