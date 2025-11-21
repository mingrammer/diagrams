"""Iterables of DOT source code lines (including final newline)."""

import typing

from . import copying

__all__ = ['Base']


class LineIterable:
    """Iterable of DOT Source code lines
        (mimics ``file`` objects in text mode)."""

    def __iter__(self) -> typing.Iterator[str]:  # pragma: no cover
        r"""Yield the generated DOT source line by line.

        Yields: Line ending with a newline (``'\n'``).
        """
        raise NotImplementedError('to be implemented by concrete subclasses')


# Common base interface for all exposed classes
class Base(LineIterable, copying.CopyBase):
    """LineIterator with ``.source`` attribute, that it returns for ``str()``."""

    @property
    def source(self) -> str:  # pragma: no cover
        raise NotImplementedError('to be implemented by concrete subclasses')

    def __str__(self) -> str:
        """The DOT source code as string."""
        return self.source
