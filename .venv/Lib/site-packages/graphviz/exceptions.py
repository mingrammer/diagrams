"""Commonly used exception classes."""

from .backend.execute import ExecutableNotFound, CalledProcessError

__all__ = ['ExecutableNotFound', 'CalledProcessError',
           'RequiredArgumentError', 'FileExistsError',
           'UnknownSuffixWarning', 'FormatSuffixMismatchWarning',
           'DotSyntaxWarning']


class RequiredArgumentError(TypeError):
    """:exc:`TypeError` raised if a required argument is missing."""


class FileExistsError(FileExistsError):
    """:exc:`FileExistsError` raised with ``raise_if_exists=True``."""


class UnknownSuffixWarning(RuntimeWarning):
    """:exc:`RuntimeWarning` raised if the suffix of ``outfile`` is unknown
        and the given ``format`` is used instead."""


class FormatSuffixMismatchWarning(UserWarning):
    """:exc:`UserWarning` raised if the suffix ``outfile``
        does not match the given ``format``."""


class DotSyntaxWarning(RuntimeWarning):
    """:exc:`RuntimeWarning` raised if a quoted string
        is expected to cause a ``CalledProcessError`` from rendering."""
