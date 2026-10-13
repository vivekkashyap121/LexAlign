import unittest

from src.lexer.python_reference import lex_python_reference


class PythonReferenceLexerTests(unittest.TestCase):
    def test_scientific_notation_is_one_number(self):
        tokens = lex_python_reference("value = 1e-5\n")
        numbers = [token for token in tokens if token.token_type == "NUMBER"]

        self.assertEqual(len(numbers), 1)
        self.assertEqual(numbers[0].value, "1e-5")
        self.assertEqual((numbers[0].start, numbers[0].end), (8, 12))

    def test_hexadecimal_is_one_number(self):
        tokens = lex_python_reference("value = 0xFF\n")
        numbers = [token for token in tokens if token.token_type == "NUMBER"]

        self.assertEqual(len(numbers), 1)
        self.assertEqual(numbers[0].value, "0xFF")

    def test_compound_operator_is_one_token(self):
        tokens = lex_python_reference("x @= 2\n")
        operators = [token for token in tokens if token.token_type == "OPERATOR"]

        self.assertEqual([token.value for token in operators], ["@="])

    def test_multiline_string_is_one_token(self):
        source = 'message = """hello\nworld"""\n'
        tokens = lex_python_reference(source)
        strings = [token for token in tokens if token.token_type == "STRING"]

        self.assertEqual(len(strings), 1)
        self.assertEqual(strings[0].value, '"""hello\nworld"""')
        self.assertEqual(source[strings[0].start:strings[0].end], strings[0].value)

    def test_unicode_identifier(self):
        tokens = lex_python_reference("café = 10\n")
        identifiers = [
            token for token in tokens if token.token_type == "IDENTIFIER"
        ]

        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0].value, "café")

    def test_indentation_tokens_are_preserved(self):
        source = "def f():\n    return 1\n"
        tokens = lex_python_reference(source, include_trivia=True)
        token_types = [token.token_type for token in tokens]

        self.assertIn("INDENT", token_types)
        self.assertIn("DEDENT", token_types)


if __name__ == "__main__":
    unittest.main()
