from antlr4 import *

from project.RaisingErrorListener import *
from project.parser.langLexer import langLexer as LangLexer
from project.parser.langParser import langParser as LangParser


def parse_stream(stream: InputStream):
    """
    Run ANTLR4 parser for language from rule program on specified stream and return parsing tree.

    If any error produced, raises RecognitionError.
    """

    lexer = LangLexer(stream)

    lexer.removeErrorListeners()
    lexer.addErrorListener(RaisingErrorListener.INSTANCE)

    parser = LangParser(CommonTokenStream(lexer))

    parser.removeErrorListeners()
    parser.addErrorListener(RaisingErrorListener.INSTANCE)

    return parser.program()


def parse(text: str = None, *, filename: str = None, encoding: str = "utf-8"):
    """
    Runs parse_stream with one of streams:

        - InputStream, if text passed,
        - FileStream, if filename passed,
        - StdinStream, if both not passed.

    Parameter encoding passed into FileStream and StdinStream.
    """

    if text is not None and filename is not None:
        raise ValueError("cannot specify both text and filename")

    if text is not None:
        stream = InputStream(text)

    elif filename is not None:
        stream = FileStream(filename, encoding=encoding)

    else:
        stream = StdinStream(encoding=encoding)

    return parse_stream(stream)


def check_syntax(text: str = None, *, filename: str = None, encoding: str = "utf-8"):
    """
    Checks is parser can recognize syntax. Parameters are similar to parse function.
    """

    try:
        parse(text=text, filename=filename, encoding=encoding)
        return True

    except RecognitionError:
        return False
