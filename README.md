# LexAlign — Token-Boundary Alignment Prototype

LexAlign is a small research prototype for measuring how a code tokenizer's source spans align with lexical tokens produced by a lightweight Python lexer.

## What the current prototype does

- Uses a lightweight regex-based lexer for a **subset** of Python, including common numeric literal forms, compound operators, multiline quoted strings, Unicode identifiers, and explicit line continuations.
- Uses Python's standard-library `tokenize` module as a reference lexer.
- Includes a differential test script to compare the lightweight lexer with the Python reference on edge-case fixtures or a directory of `.py` files.
- Loads the `bigcode/starcoder2-3b` tokenizer.
- Compares tokenizer offset spans with lexer spans.
- Reports whole-lexeme, sub-lexeme, boundary-straddling, unclassified, and zero-length cases.
- Separately records whether a tokenizer span covers code, whitespace, comments, or a mixture.
- Includes a small test suite that runs without downloading a model.

## Important research limitations

This is a measurement prototype, not evidence of research novelty by itself. The lexer is not a complete implementation of Python's lexical specification. Before using results in a paper, validate the lexer against a broader corpus, specify the whitespace/trivia policy, test offset reconstruction, and compare against baselines.

The custom regex lexer is still not a complete implementation of Python's lexical specification. In particular, f-string internals (which newer Python versions expose as separate tokens), and some advanced or version-specific syntax may differ from the standard-library reference. The differential test script currently identifies the f-string fixture as a known mismatch; do not describe the custom lexer as fully Python-compliant.

The current alignment categories are occurrence-based. A token that includes leading whitespace and exactly one complete code lexeme can still be `WHOLE_LEXEME`; whitespace involvement is recorded separately. A tokenizer token overlapping multiple meaningful lexer tokens is `BOUNDARY_STRADDLING`.

## Requirements

- Python 3.10 or newer (Python 3.11/3.12 are good choices; your existing Python 3.13 may work).
- Internet access on the first real-tokenizer run to download the Hugging Face tokenizer files.

## Setup on macOS (zsh)

Open Terminal and run these commands one at a time:

```bash
cd ~/Desktop
mkdir LexAlign_Fresh
cd LexAlign_Fresh
```

If you downloaded and extracted this project ZIP, **do not create the folder again**. Instead, `cd` into the extracted `LexAlign_Fresh` folder.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the tests first:

```bash
python -m unittest discover -s tests -v
```

Run the differential check on built-in edge-case fixtures:

```bash
python scripts/differential_test.py
```

Compare the lexer with Python's `tokenize` module on up to 500 Python files in a directory:

```bash
python scripts/differential_test.py path/to/python/source --limit 500
```
The differential script reports mismatches rather than assuming the custom lexer is correct. Some mismatches, including f-string internals, are currently expected and must be documented or fixed before using the custom lexer as a reference.

Run the alignment experiment:

```bash
python run_alignment.py
```

The first run downloads tokenizer files and may take some time. PyTorch is not required for tokenizer-only inspection. If Transformers warns that PyTorch is missing, that warning alone does not prevent tokenizer-only work.

## Files

```text
LexAlign_Fresh/
├── README.md
├── requirements.txt
├── run_alignment.py
├── src/
│   ├── __init__.py
│   ├── lexer/
│   │   ├── __init__.py
│   │   ├── tokens.py
│   │   ├── lexer.py
│   │   └── python_reference.py
│   └── alignment/
│       ├── __init__.py
│       ├── profile.py
│       └── metrics.py
├── scripts/
│   └── differential_test.py
└── tests/
    ├── test_alignment.py
    ├── test_metrics.py
    └── test_python_reference.py
```

## Interpreting the output

- `WHOLE_LEXEME`: the non-whitespace source characters in a tokenizer token match one complete meaningful lexer token.
- `SUB_LEXEME`: the tokenizer token covers only part of one meaningful lexer token.
- `BOUNDARY_STRADDLING`: the tokenizer token overlaps more than one meaningful lexer token.
- `UNCLASSIFIED`: no meaningful lexer token overlaps the tokenizer span (e.g. whitespace-only or comment-only spans).
- `ZERO_LENGTH`: the tokenizer returned an empty source span.

The whitespace/trivia dimension is reported separately. Therefore, a token like a leading space plus `=` is not automatically treated as a lexical boundary-straddling case.

## Next research steps

1. Validate lexer coverage and document unsupported syntax.
2. Add a corpus of code snippets and reproducible dataset splits.
3. Compare alignment scores across multiple tokenizers.
4. Implement baselines and a tokenizer-vocabulary-constrained retokenization algorithm.
5. Evaluate exact source reconstruction, token-count inflation, runtime, and downstream model behavior.
