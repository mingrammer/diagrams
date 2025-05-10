import argparse
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
        with open(path, encoding='utf-8') as f:
            exec(f.read())

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
