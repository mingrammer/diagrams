import argparse
import runpy
import sys


def run() -> int:
    """
    Run diagrams code files in a diagrams environment.
    Args:
        paths: A list of paths to Python files containing diagrams code.

    Returns:
        The exit code.
    """
    parser = argparse.ArgumentParser(
        description="Run diagrams code files in a diagrams environment.",
    )
    parser.add_argument(
        "paths",
        metavar="path",
        type=str,
        nargs="+",
        help="a Python file containing diagrams code",
    )
    args = parser.parse_args()

    for path in args.paths:
        runpy.run_path(path, run_name="__main__")

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
