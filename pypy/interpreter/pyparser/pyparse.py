from pypy.interpreter.error import OperationError
from pypy.interpreter.pyparser import future, parser, pytokenizer, pygram, error, pytoken
from pypy.interpreter.astcompiler import consts
from pypy.module.sys.version import CPYTHON_VERSION
from rpython.rlib import rstring

CPYTHON_MINOR_VERSION = CPYTHON_VERSION[1]

def recode_to_utf8(space, bytes, encoding):
    if encoding == 'utf-8':
        return bytes
    w_text = space.call_method(space.newbytes(bytes), "decode",
                               space.newtext(encoding))
    w_recoded = space.call_method(w_text, "encode", space.newtext("utf-8"))
    return space.bytes_w(w_recoded)

def _normalize_encoding(encoding):
    """returns normalized name for <encoding>

    see dist/src/Parser/tokenizer.c 'get_normal_name()'
    for implementation details / reference

    NOTE: for now, parser.suite() raises a MemoryError when
          a bad encoding is used. (SF bug #979739)
    """
    if encoding is None:
        return None
    # lower() + '_' / '-' conversion
    encoding = encoding.replace('_', '-').lower()
    if encoding == 'utf-8' or encoding.startswith('utf-8-'):
        return 'utf-8'
    for variant in ['latin-1', 'iso-latin-1', 'iso-8859-1']:
        if (encoding == variant or
            encoding.startswith(variant + '-')):
            return 'iso-8859-1'
    return encoding

def _check_for_encoding(s):
    eol = s.find('\n')
    if eol < 0:
        return _check_line_for_encoding(s)[0]
    enc, again = _check_line_for_encoding(s[:eol])
    if enc or not again:
        return enc
    eol2 = s.find('\n', eol + 1)
    if eol2 < 0:
        return _check_line_for_encoding(s[eol + 1:])[0]
    return _check_line_for_encoding(s[eol + 1:eol2])[0]


def _check_line_for_encoding(line):
    """returns the declared encoding or None"""
    i = 0
    for i in range(len(line)):
        if line[i] == '#':
            break
        if line[i] not in ' \t\014':
            return None, False  # Not a comment, don't read the second line.
    return pytokenizer.match_encoding_declaration(line[i:]), True


class CompileInfo(object):
    """Stores information about the source being compiled.

    * filename: The filename of the source.
    * mode: The parse mode to use. ('exec', 'eval', 'single' or 'func_type')
    * flags: Parser and compiler flags.
    * encoding: The source encoding.
    * last_future_import: The line number and offset of the last __future__
      import.
    * hidden_applevel: Will this code unit and sub units be hidden at the
      applevel?
    * optimize: optimization level:
         0 = no optmiziation,
         1 = remove asserts,
         2 = remove docstrings.
    """

    def __init__(self, filename, mode="exec", flags=0, future_pos=(0, 0),
                 hidden_applevel=False, optimize=0, feature_version=-1):
        assert optimize >= 0
        if feature_version == -1:
            feature_version = CPYTHON_MINOR_VERSION
        if feature_version < 7:
            flags |= consts.PyCF_ASYNC_HACKS
        rstring.check_str0(filename)
        self.filename = filename
        self.mode = mode
        self.encoding = None
        self.flags = flags
        self.optimize = optimize
        self.last_future_import = future_pos
        self.hidden_applevel = hidden_applevel
        self.feature_version = feature_version


class PythonParser(object): # leave class for mergeability of _handle_encoding

    @staticmethod
    def _handle_encoding(bytessrc, compile_info, space):
        # Detect source encoding. also updates compile_info.flags
        explicit_encoding = False
        enc = None
        if compile_info.flags & consts.PyCF_SOURCE_IS_UTF8:
            enc = 'utf-8'

        if compile_info.flags & consts.PyCF_IGNORE_COOKIE:
            textsrc = bytessrc
        elif bytessrc.startswith("\xEF\xBB\xBF"):
            bytessrc = bytessrc[3:]
            enc = 'utf-8'
            # If an encoding is explicitly given check that it is utf-8.
            decl_enc = _check_for_encoding(bytessrc)
            explicit_encoding = (decl_enc is not None)
            if decl_enc and _normalize_encoding(decl_enc) != "utf-8":
                raise error.SyntaxError("UTF-8 BOM with %s coding cookie" % decl_enc,
                                        filename=compile_info.filename)
            textsrc = bytessrc
        else:
            enc = _normalize_encoding(_check_for_encoding(bytessrc))
            explicit_encoding = (enc is not None)
            if enc is None:
                enc = 'utf-8'
            try:
                textsrc = recode_to_utf8(space, bytessrc, enc)
            except OperationError as e:
                # if the codec is not found, LookupError is raised.  we
                # check using 'is_w' not to mask potential IndexError or
                # KeyError
                if e.match(space, space.w_LookupError):
                    raise error.SyntaxError("Unknown encoding: %s" % enc,
                                            filename=compile_info.filename)
                # Transform unicode errors into SyntaxError
                if e.match(space, space.w_UnicodeDecodeError):
                    e.normalize_exception(space)
                    w_message = space.str(e.get_w_value(space))
                    raise error.SyntaxError(space.text_w(w_message))
                raise
        if enc is not None:
            compile_info.encoding = enc
        if explicit_encoding:
            compile_info.flags |= consts.PyCF_FOUND_ENCODING
        return textsrc

    @staticmethod
    def _check_token_stream_single(compile_info, tokens_stream):
        for token in tokens_stream:
            if token.token_type == pygram.tokens.ENDMARKER:
                break
            if token.token_type == pygram.tokens.NEWLINE:
                continue

            if token.token_type == pygram.tokens.COMMENT:
                for token in tokens_stream:
                    if token.token_type == pygram.tokens.NEWLINE:
                        break
            else:
                new_err = error.SyntaxError
                msg = ("multiple statements found while "
                       "compiling a single statement")
                raise new_err(msg, token.lineno, token.column,
                              token.line, compile_info.filename)

class PegParser(object):
    def __init__(self, space, future_flags=future.futureFlags_3_9):
        self.space = space
        self.future_flags = future_flags
        self.type_ignores = []

    def reset(self):
        pass

    def parse_source(self, bytessrc, compile_info):
        """Main entry point for parsing Python source.

        Everything from decoding the source to tokenizing to building the parse
        tree is handled here.
        """
        textsrc = PythonParser._handle_encoding(bytessrc, compile_info, self.space)
        return self._parse(textsrc, compile_info)

    def _parse(self, textsrc, compile_info):
        from pypy.interpreter.pyparser.rpypegparse import PythonParser
        # XXX too much copy-paste
        flags = compile_info.flags

        # The tokenizer is very picky about how it wants its input.
        source_lines = textsrc.splitlines(True)
        if source_lines and not source_lines[-1].endswith("\n"):
            source_lines[-1] += '\n'
        if textsrc and textsrc[-1] == "\n" or compile_info.mode != "single":
            flags &= ~consts.PyCF_DONT_IMPLY_DEDENT

        try:
            # Note: we no longer pass the CO_FUTURE_* to the tokenizer,
            # which is expected to work independently of them.  It's
            # certainly the case for all futures in Python <= 2.7.
            tokens = pytokenizer.generate_tokens(source_lines, flags)
        except error.TokenError as e:
            if (compile_info.flags & consts.PyCF_ALLOW_INCOMPLETE_INPUT and
                    (pytokenizer.TRIPLE_QUOTE_UNTERMINATED_ERROR in e.msg or
                     'was never closed' in e.msg)):
                e.msg = "incomplete input"
            e.filename = compile_info.filename
            raise
        except error.TokenIndentationError as e:
            e.filename = compile_info.filename
            raise


        newflags, last_future_import = (
            future.add_future_flags(self.future_flags, tokens))
        compile_info.last_future_import = last_future_import
        compile_info.flags |= newflags

        mode = compile_info.mode
        if mode != "single":
            assert tokens[-2].token_type == pytoken.python_tokens['NEWLINE']
            del tokens[-2]
        pp = PythonParser(self.space, tokens, compile_info)
        try:
            for token in tokens:
                # Special handling for TYPE_IGNOREs
                if token.token_type == pygram.tokens.TYPE_IGNORE:
                    self.type_ignores.append(token)
            if mode == "exec":
                meth = PythonParser.file
            elif mode == "single":
                meth = PythonParser.interactive
            elif mode == "eval":
                meth = PythonParser.eval
            elif mode == "func_type":
                meth = PythonParser.func_type
            else:
                assert 0, "unknown mode"
            return pp.parse_meth_or_raise(meth)
        except error.TokenError as e:
            e.filename = compile_info.filename
            raise
        except error.TokenIndentationError as e:
            e.filename = compile_info.filename
            raise


