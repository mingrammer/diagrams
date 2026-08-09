"""Fail a release when the git tag disagrees with the version in pyproject.toml.

Issue #1183: the `v0.24.4` tag was placed on a commit whose pyproject.toml still
read `version = "0.24.3"`, so the tag, the sdist and the PyPI release all
disagreed and downstream packagers could not tell which was authoritative.
Nothing in the repository checked for that, so it went unnoticed.

Run as `python -m scripts.check_release_version v0.25.2`, or with no argument to
pick the tag up from `$GITHUB_REF_NAME`. Reading pyproject.toml requires
Python 3.11+ (tomllib); the tag-version workflow runs it on 3.12.
"""

import os
import sys
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


class ReleaseCheckError(Exception):
    """Raised when the release tag and pyproject.toml cannot be reconciled."""


def project_version(pyproject: Path = PYPROJECT) -> str:
    """Return the `version` declared in the [project] table of pyproject.toml."""
    try:
        import tomllib
    except ModuleNotFoundError as exc:  # Python < 3.11
        raise ReleaseCheckError(
            "reading pyproject.toml requires Python 3.11+ (tomllib); "
            "the tag-version workflow runs this check on 3.12"
        ) from exc

    try:
        with open(pyproject, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as exc:
        raise ReleaseCheckError(f"could not read the [project] version from {pyproject}: {exc!r}") from exc


def check_tag(tag: str, version: str) -> None:
    """Raise ReleaseCheckError unless `tag` names exactly `version`."""
    normalized = tag[1:] if tag.startswith("v") else tag
    if normalized != version:
        raise ReleaseCheckError(
            f"git tag {tag!r} does not match the project version {version!r} in pyproject.toml. "
            f"Bump the version and tag that commit, or move the tag."
        )


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    tag = argv[0] if argv else os.environ.get("GITHUB_REF_NAME", "")
    if not tag:
        print("usage: python -m scripts.check_release_version <tag>", file=sys.stderr)
        return 2

    try:
        version = project_version()
        check_tag(tag, version)
    except ReleaseCheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"ok: tag {tag} matches pyproject.toml version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
