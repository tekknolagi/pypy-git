# -*- coding: utf-8 -* -
import pytest
from pypy.interpreter.astcompiler import consts
from pypy.interpreter.pyparser import pytokenizer
from pypy.interpreter.pyparser.parser import Token
from pypy.interpreter.pyparser.pygram import tokens
from pypy.interpreter.pyparser.error import TokenError

def tokenize(s, flags=0):
    source_lines = s.splitlines(True)
    if source_lines and not source_lines[-1].endswith("\n"):
        source_lines[-1] += '\n'
    return pytokenizer.generate_tokens(source_lines, flags)

def check_token_error(s, msg=None, pos=-1, line=-1):
    error = pytest.raises(TokenError, tokenize, s)
    if msg is not None:
        assert error.value.msg == msg
    if pos != -1:
        assert error.value.offset == pos
    if line != -1:
        assert error.value.lineno == line


class TestTokenizer(object):

    def test_simple(self):
        line = "a+1\n"
        tks = tokenize(line)
        assert tks[:-3] == [
            Token(tokens.NAME, 'a', 1, 0, line, 1, 1),
            Token(tokens.PLUS, '+', 1, 1, line, 1, 2),
            Token(tokens.NUMBER, '1', 1, 2, line, 1, 3),
            ]

    def test_error_parenthesis(self):
        for paren in "([{":
            check_token_error(paren + "1 + 2",
                              "'%s' was never closed" % paren,
                              1)

        for paren in ")]}":
            check_token_error("1 + 2" + paren,
                              "unmatched '%s'" % (paren, ),
                              6)

        for i, opening in enumerate("([{"):
            for j, closing in enumerate(")]}"):
                if i == j:
                    continue
                check_token_error(opening + "1\n" + closing,
                        "closing parenthesis '%s' does not match opening parenthesis '%s' on line 1" % (closing, opening),
                        pos=1, line=2)
                check_token_error(opening + "1" + closing,
                        "closing parenthesis '%s' does not match opening parenthesis '%s'" % (closing, opening),
                        pos=3, line=1)
                check_token_error(opening + closing,
                        "closing parenthesis '%s' does not match opening parenthesis '%s'" % (closing, opening),
                        pos=2, line=1)


    def test_unknown_char(self):
        check_token_error("?", "Unknown character", 1)

    def test_eol_string(self):
        check_token_error("x = 'a", pos=5, line=1)

    def test_eof_triple_quoted(self):
        check_token_error("'''", pos=1, line=1)

    def test_type_comments(self):
        line = "a = 5 # type: int\n"
        tks = tokenize(line, flags=consts.PyCF_TYPE_COMMENTS)
        assert tks[:-3] == [
            Token(tokens.NAME, 'a', 1, 0, line, 1, 1),
            Token(tokens.EQUAL, '=', 1, 2, line, 1, 3),
            Token(tokens.NUMBER, '5', 1, 4, line, 1, 5),
            Token(tokens.TYPE_COMMENT, 'int', 1, 6, line),
        ]

    def test_type_comment_bug(self):
        lines = ['# type: int\n', '']
        pytokenizer.generate_tokens(lines, flags=consts.PyCF_TYPE_COMMENTS)

    def test_type_ignore(self):
        line = "a = 5 # type: ignore@teyit\n"
        tks = tokenize(line, flags=consts.PyCF_TYPE_COMMENTS)
        assert tks[:-3] == [
            Token(tokens.NAME, 'a', 1, 0, line, 1, 1),
            Token(tokens.EQUAL, '=', 1, 2, line, 1, 3),
            Token(tokens.NUMBER, '5', 1, 4, line, 1, 5),
            Token(tokens.TYPE_IGNORE, '@teyit', 1, 6, line),
        ]

    def test_walrus(self):
        line = "a:=1\n"
        tks = tokenize(line)
        assert tks[:-3] == [
            Token(tokens.NAME, 'a', 1, 0, line, 1, 1),
            Token(tokens.COLONEQUAL, ':=', 1, 1, line, 1, 3),
            Token(tokens.NUMBER, '1', 1, 3, line, 1, 4),
            ]

    def test_triple_quoted(self):
        input = '''x = """
hello
content
whatisthis""" + "a"\n'''
        s = '''"""
hello
content
whatisthis"""'''
        tks = tokenize(input)
        lines = input.splitlines(True)
        assert tks[:3] == [
            Token(tokens.NAME, 'x', 1, 0, lines[0], 1, 1),
            Token(tokens.EQUAL, '=', 1, 2, lines[0], 1, 3),
            Token(tokens.STRING, s, 1, 4, lines[3], 4, 13),
        ]

    def test_parenthesis_positions(self):
        input = '( ( ( a ) ) ) ( )'
        tks = tokenize(input)[:-3]
        columns = [t.column for t in tks]
        assert columns == [0, 2, 4, 6, 8, 10, 12, 14, 16]
        assert [t.end_column - 1 for t in tks] == columns

    def test_PyCF_DONT_IMPLY_DEDENT(self):
        input = "if 1:\n  1\n"
        # regular mode
        tks = tokenize(input)
        lines = input.splitlines(True)
        del tks[-2] # new parser deletes one newline anyway
        assert tks == [
            Token(tokens.NAME, 'if', 1, 0, lines[0], 1, 2),
            Token(tokens.NUMBER, '1', 1, 3, lines[0], 1, 4),
            Token(tokens.COLON, ':', 1, 4, lines[0], 1, 5),
            Token(tokens.NEWLINE, '', 1, 5, lines[0], -1, -1),
            Token(tokens.INDENT, '  ', 2, 0, lines[1], 2, 2),
            Token(tokens.NUMBER, '1', 2, 2, lines[1], 2, 3),
            Token(tokens.NEWLINE, '', 2, 3, lines[1], -1, -1),
            Token(tokens.DEDENT, '', 2, 0, '', -1, -1),
            Token(tokens.ENDMARKER, '', 2, 0, '', -1, -1),
        ]
        # single mode
        tks = tokenize(input, flags=consts.PyCF_DONT_IMPLY_DEDENT)
        lines = input.splitlines(True)
        del tks[-2] # new parser deletes one newline anyway
        assert tks == [
            Token(tokens.NAME, 'if', 1, 0, lines[0], 1, 2),
            Token(tokens.NUMBER, '1', 1, 3, lines[0], 1, 4),
            Token(tokens.COLON, ':', 1, 4, lines[0], 1, 5),
            Token(tokens.NEWLINE, '', 1, 5, lines[0], -1, -1),
            Token(tokens.INDENT, '  ', 2, 0, lines[1], 2, 2),
            Token(tokens.NUMBER, '1', 2, 2, lines[1], 2, 3),
            Token(tokens.NEWLINE, '', 2, 3, lines[1], -1, -1),
            Token(tokens.ENDMARKER, '', 2, 0, '', -1, -1),
        ]

    def test_ignore_just_linecont(self):
        input = "pass\n    \\\n\npass"
        tks = tokenize(input)
        tps = [tk.token_type for tk in tks]
        assert tps == [tokens.NAME, tokens.NEWLINE, tokens.NAME,
                tokens.NEWLINE, tokens.NEWLINE, tokens.ENDMARKER]

    def test_error_linecont(self):
        check_token_error("a \\ b",
                          "unexpected character after line continuation character",
                          4)

    def test_error_integers(self):
        check_token_error("0b106",
                "invalid digit '6' in binary literal",
                5)
        check_token_error("0b10_6",
                "invalid digit '6' in binary literal",
                5)
        check_token_error("0b6",
                "invalid digit '6' in binary literal",
                3)
        check_token_error("0b \n",
                "invalid binary literal",
                2)
        check_token_error("0o129",
                "invalid digit '9' in octal literal",
                5)
        check_token_error("0o12_9",
                "invalid digit '9' in octal literal",
                5)
        check_token_error("0o9",
                "invalid digit '9' in octal literal",
                3)
        check_token_error("0o \n",
                "invalid octal literal",
                2)
        check_token_error("0x1__ \n",
                "invalid hexadecimal literal",
                4)
        check_token_error("0x\n",
                "invalid hexadecimal literal",
                2)
        check_token_error("1_ \n",
                "invalid decimal literal",
                2)
        check_token_error("0b1_ \n",
                "invalid binary literal",
                3)
        check_token_error("01212 \n",
                "leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers",
                1)
        tokenize("1 2 \n") # does not raise
        tokenize("1 _ \n") # does not raise


    def test_invalid_identifier(self):
        check_token_error("aänc€",
                "invalid character '€' (U+20AC)",
                6)
        check_token_error("a\xc2\xa0b",
                "invalid non-printable character U+00A0",
                2)

class TestTokenizer310Changes(object):
    def test_single_quoted(self):
        check_token_error('s = "abc\n', "unterminated string literal (detected at line 1)", pos=5)

    def test_triple_quoted(self):
        check_token_error('"""abc\n', "unterminated triple-quoted string literal (detected at line 1)")

    def test_single_quoted_detected(self):
        check_token_error('s = "abc\n', "unterminated string literal (detected at line 1)")
        check_token_error('s = "abc\\\na\\\nb\n', "unterminated string literal (detected at line 3)", pos=5)

    def test_triple_quoted_detected(self):
        check_token_error('s = """', "unterminated triple-quoted string literal (detected at line 1)")
        check_token_error('s = """abc\\\na\\\nb\n\n\n\n\n', "unterminated triple-quoted string literal (detected at line 7)")

    def test_warn_number_followed_by_keyword(self):
        line = "0x1for\n"
        tks = tokenize(line)
        assert tks[:-3] == [
            Token(tokens.NUMBER, '0x1f', 1, 0, line, 1, 4),
            Token(tokens.WARNING, 'invalid hexadecimal literal', 1, 0, line),
            Token(tokens.NAME, 'or', 1, 4, line, 1, 6),
            ]

        for line in ("1in 3", "0b01010111and 4", "1 if 0o21231else 2"):
            tks = tokenize(line)
            assert any(tokens.WARNING == tok.token_type for tok in tks)


    def test_error_number_by_non_keyword_name(self):
        check_token_error("1a 2", "invalid decimal literal")

    def test_levels(self):
        line = 'a b (c + d) [[e, f]]'
        tks = tokenize(line)
        levels = [token.level for token in tks]
        assert levels == [0, 0, 1, 1, 1, 1, 0, 1, 2, 2, 2, 2, 1, 0, 0, 0, 0]
