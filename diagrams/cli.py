import argparse
import sys


def run() -> int:
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
        print(path)
        with open(path) as f:
            exec(f.read())

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
