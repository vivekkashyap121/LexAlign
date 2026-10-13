import unittest

from src.alignment.profile import build_alignment_profile
from src.alignment.metrics import calculate_alignment_metrics


class FakeTokenizer:
    """A deterministic tokenizer stub for testing metrics."""

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


class MetricsTests(unittest.TestCase):
    def test_alignment_category_counts_sum_to_total(self):
        profile = build_alignment_profile("x = 1", FakeTokenizer())
        metrics = calculate_alignment_metrics(profile)

        category_names = [
            "whole_lexeme",
            "sub_lexeme",
            "boundary_straddling",
            "trivia_mixed",
            "unclassified",
            "zero_length",
        ]

        category_total = sum(
            metrics[f"{name}_count"] for name in category_names
        )

        self.assertEqual(category_total, metrics["total_tokens"])

    def test_alignment_category_ratios_sum_to_one(self):
        profile = build_alignment_profile("x = 1", FakeTokenizer())
        metrics = calculate_alignment_metrics(profile)

        category_names = [
            "whole_lexeme",
            "sub_lexeme",
            "boundary_straddling",
            "trivia_mixed",
            "unclassified",
            "zero_length",
        ]

        ratio_total = sum(
            metrics[f"{name}_ratio"] for name in category_names
        )

        self.assertAlmostEqual(ratio_total, 1.0)

    def test_trivia_mixed_metric_is_present(self):
        profile = build_alignment_profile("x = 1", FakeTokenizer())
        metrics = calculate_alignment_metrics(profile)

        self.assertIn("trivia_mixed_count", metrics)
        self.assertIn("trivia_mixed_ratio", metrics)

    def test_empty_source_has_zero_ratios(self):
        profile = build_alignment_profile("", FakeTokenizer())
        metrics = calculate_alignment_metrics(profile)

        self.assertEqual(metrics["total_tokens"], 0)
        self.assertEqual(metrics["whole_lexeme_ratio"], 0.0)
        self.assertEqual(metrics["trivia_mixed_ratio"], 0.0)
        self.assertEqual(metrics["exact_boundary_match_ratio"], 0.0)


if __name__ == "__main__":
    unittest.main()
