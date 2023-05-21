#!/usr/bin/env python3

import subprocess
import shared
import os


def main():
    shared.configure_python_path()

    os.chdir("./project")
    subprocess.check_call(
        [
            "antlr4",
            "-v",
            "4.13.0",
            "-Dlanguage=Python3",
            "-no-listener",
            "-visitor",
            "-o",
            "parser",
            "lang.g4",
        ]
    )


if __name__ == "__main__":
    main()
