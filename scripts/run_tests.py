#!/usr/bin/env python3

import subprocess
import shared
import sys


def main():
    shared.configure_python_path()

    if len(sys.argv) == 2:
        subprocess.check_call(["pytest", "-vv", "-s", sys.argv[1]])

    else:
        subprocess.check_call(["pytest", "-vv", "-s", shared.TESTS])


if __name__ == "__main__":
    main()
