from antlr4.error.ErrorListener import ErrorListener


class RecognitionError(ValueError):
    def __init__(self, kind: str, **kwargs):
        super().__init__(
            f"{kind}({', '.join([f'{k} = {v.__repr__()}' for k, v in kwargs.items()])})"
        )

        self.kind = kind
        self.values = kwargs


class RaisingErrorListener(ErrorListener):

    INSTANCE = None

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise RecognitionError(
            "syntaxError",
            recognizer=recognizer,
            offendingSymbol=offendingSymbol,
            line=line,
            column=column,
            msg=msg,
            e=e,
        )

    def reportAmbiguity(
        self,
        recognizer,
        dfa,
        startIndex,
        stopIndex,
        exact,
        ambigAlts,
        configs,
    ):
        raise RecognitionError(
            "reportAmbiguity",
            recognizer=recognizer,
            dfa=dfa,
            startIndex=startIndex,
            stopIndex=stopIndex,
            exact=exact,
            ambigAlts=ambigAlts,
            configs=configs,
        )

    def reportAttemptingFullContext(
        self,
        recognizer,
        dfa,
        startIndex,
        stopIndex,
        conflictingAlts,
        configs,
    ):
        raise RecognitionError(
            "reportAttemptingFullContext",
            recognizer=recognizer,
            dfa=dfa,
            startIndex=startIndex,
            stopIndex=stopIndex,
            exact=exact,
            conflictingAlts=conflictingAlts,
            configs=configs,
        )

    def reportContextSensitivity(
        self,
        recognizer,
        dfa,
        startIndex,
        stopIndex,
        prediction,
        configs,
    ):
        raise RecognitionError(
            "reportContextSensitivity",
            dfa=dfa,
            startIndex=startIndex,
            stopIndex=stopIndex,
            exact=exact,
            prediction=prediction,
            configs=configs,
        )


RaisingErrorListener.INSTANCE = RaisingErrorListener()
