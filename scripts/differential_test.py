"""Compare the lightweight regex lexer with Python's tokenize module.

Usage:
    python scripts/differential_test.py
    python scripts/differential_test.py path/to/python/files --limit 500

The script compares significant token source spans and values. It deliberately
reports differences rather than assuming the lightweight lexer is authoritative.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lexer.lexer import lex
from src.lexer.python_reference import lex_python_reference

IGNORED = {"WHITESPACE", "COMMENT", "NEWLINE", "NL", "INDENT", "DEDENT"}

FIXTURES = {
    "scientific notation": "value = 1e-5\n",
    "hexadecimal": "value = 0xFF\n",
    "underscored integer": "value = 1_000\n",
    "imaginary number": "value = 3j\n",
    "matrix multiply assignment": "x @= 2\n",
    "triple single string": "message = '''hello\\nworld'''\n",
    "triple double string": 'message = """hello\\nworld"""\n',
    "unicode identifier": "café = 10\n",
    "line continuation": "value = 1 + \\\n    2\n",
    "operators": "x **= 2; y //= 3; z <<= 1\n",
    "f-string": 'message = f"value={value}"\n',
    "nested indentation": "def f(x):\n    if x > 0:\n        return x\n    return 0\n",
}


def signature(tokens):
    return [(t.token_type, t.value, t.start, t.end) for t in tokens if t.token_type not in IGNORED]


def check_source(label: str, source: str) -> tuple[int, list[str]]:
    try:
        custom = signature(lex(source))
    except Exception as exc:  # report crashes as differences too
        return 1, [f"{label}: custom lexer raised {type(exc).__name__}: {exc}"]
    try:
        reference = signature(lex_python_reference(source))
    except Exception as exc:
        return 1, [f"{label}: Python reference raised {type(exc).__name__}: {exc}"]

    # Type aliases intentionally differ in this prototype, so compare exact
    # source text and offsets first; type differences are shown separately.
    custom_spans = [(value, start, end) for _, value, start, end in custom]
    reference_spans = [(value, start, end) for _, value, start, end in reference]
    if custom_spans == reference_spans:
        return 0, []
    lines = [f"{label}: token span/value mismatch"]
    max_len = max(len(custom), len(reference))
    for i in range(max_len):
        c = custom[i] if i < len(custom) else None
        r = reference[i] if i < len(reference) else None
        if c != r:
            lines.append(f"  token {i}: custom={c!r}; python={r!r}")
            if len(lines) >= 8:
                lines.append("  ... (remaining differences omitted)")
                break
    return 1, lines


def iter_files(path: Path, limit: int):
    if path.is_file():
        yield path
        return
    count = 0
    for candidate in sorted(path.rglob("*.py")):
        if any(part in {".git", ".venv", "venv", "site-packages", "__pycache__"} for part in candidate.parts):
            continue
        yield candidate
        count += 1
        if count >= limit:
            break


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="Python file or directory; defaults to built-in edge-case fixtures")
    parser.add_argument("--limit", type=int, default=500, help="maximum Python files to scan from a directory (default: 500)")
    args = parser.parse_args()

    failures = 0
    total = 0
    if args.path is None:
        sources = FIXTURES.items()
        for label, source in sources:
            total += 1
            count, messages = check_source(label, source)
            failures += count
            for message in messages:
                print(message)
    else:
        if not args.path.exists():
            parser.error(f"path does not exist: {args.path}")
        files = list(iter_files(args.path, args.limit))
        for file_path in files:
            total += 1
            try:
                source = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                print(f"SKIP {file_path}: {exc}")
                continue
            count, messages = check_source(str(file_path), source)
            failures += count
            for message in messages:
                print(message)

    print(f"\nDifferential test summary: {total - failures}/{total} sources matched; {failures} source(s) had differences.")
    print("Note: differences are diagnostic; Python's tokenize module is the reference, not the custom lexer.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
