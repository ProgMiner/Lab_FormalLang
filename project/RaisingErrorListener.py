from antlr4.error.ErrorListener import ErrorListener


class RecognitionError(ValueError):
    def __init__(self, **kwargs):
        super().__init__(kwargs)

        self.values = kwargs


class RaisingErrorListener(ErrorListener):

    INSTANCE = None

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise RecognitionError(
            recognizer=recognizer,
            offendingSymbol=offendingSymbol,
            line=line,
            column=column,
            msg=msg,
            e=e,
        )


RaisingErrorListener.INSTANCE = RaisingErrorListener()
