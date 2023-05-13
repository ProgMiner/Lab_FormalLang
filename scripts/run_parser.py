#!/usr/bin/env python3

import shared
import sys


if __name__ == "__main__":
    sys.path.insert(1, str(shared.ROOT))

    from project.lang import parse, write_to_dot

    write_to_dot(parse(), "result.dot")
