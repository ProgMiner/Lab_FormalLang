#!/usr/bin/env python3

import traceback
import shared
import sys

DEBUG = False


if __name__ == "__main__":
    sys.path.insert(1, str(shared.ROOT))

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None

    from project.lang import parse, RecognitionError
    from project.interpreter import interpret, InterpretError

    try:
        interpret(parse(filename=filename))

    except RecognitionError as e:
        print(
            f'Parsing error at {e.values["line"]}:{e.values["column"]}: {e.values["msg"]}'
        )

        if DEBUG:
            traceback.print_exc()

    except InterpretError as e:
        print(f"Runtime error at {e}")

        if DEBUG:
            traceback.print_exc()
