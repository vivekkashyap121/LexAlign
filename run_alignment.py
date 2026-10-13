from transformers import AutoTokenizer

from src.alignment.profile import build_alignment_profile
from src.alignment.metrics import (
    calculate_alignment_metrics,
    print_alignment_metrics,
)

MODEL_NAME = "bigcode/starcoder2-3b"

EXPERIMENTS = {
    "1. Simple assignments": """x = 10
y = x + 5
""",
    "2. Identifiers with underscores": """total_marks = 95
average_marks = total_marks / 2
""",
    "3. Multi-character operators": """if score >= 50 and count != 0:
    result = score // count
""",
    "4. Function definition": """def calculate_average(total, count):
    return total / count
""",
    "5. String literals": '''message = "Hello, Python!"
path = "folder/file.py"
''',
    "6. Comments and indentation": """# Calculate the result
if value > 0:
    result = value + 1
""",
}


def main():
    print(f"Loading tokenizer: {MODEL_NAME}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    if not getattr(tokenizer, "is_fast", False):
        raise RuntimeError(
            "A fast tokenizer is required for offset_mapping."
        )

    print("Tokenizer loaded successfully.")

    summary = []
    reference_modes = ["custom", "python"]

    for experiment_name, source in EXPERIMENTS.items():
        print("\n" + "=" * 70)
        print(experiment_name)
        print("=" * 70)
        print("\nSource code:\n")
        print(source)

        for reference in reference_modes:
            print(f"\n--- Reference lexer: {reference} ---")
            profile = build_alignment_profile(
                source, tokenizer, reference=reference
            )
            metrics = calculate_alignment_metrics(profile)
            print_alignment_metrics(metrics)

            summary.append({
                "name": experiment_name,
                "reference": reference,
                "metrics": metrics,
            })

            print("\nToken details:")
        for item in profile["tokens"]:
            print(
                f"{item['category']:<22} "
                f"Span=({item['start']:>3}, {item['end']:>3}) "
                f"Token={item['token']!r:<18} "
                f"Source={item['source_text']!r} "
                f"LexerTypes={item['overlapping_lexer_types']} "
                f"ExactBoundary={item['exact_boundary_match']}"
            )

    print("\n" + "=" * 70)
    print("COMPARATIVE SUMMARY")
    print("=" * 70)

    print(
        f"{'Experiment':<34}"
        f"{'Tokens':>8}"
        f"{'Whole %':>10}"
        f"{'Sub %':>10}"
        f"{'Straddle %':>13}"
        f"{'Exact %':>10}"
        f"{'Reference':>12}"
    )

    for item in summary:
        metrics = item["metrics"]
        print(
            f"{item['name']:<34}"
            f"{metrics['total_tokens']:>8}"
            f"{metrics['whole_lexeme_ratio'] * 100:>9.2f}%"
            f"{metrics['sub_lexeme_ratio'] * 100:>9.2f}%"
            f"{metrics['boundary_straddling_ratio'] * 100:>12.2f}%"
            f"{metrics['exact_boundary_match_ratio'] * 100:>9.2f}%"
            f"{item['reference']:>12}"
        )


if __name__ == "__main__":
    main()
