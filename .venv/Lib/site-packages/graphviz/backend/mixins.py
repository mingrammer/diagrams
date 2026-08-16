"""Mixin classes used by Base subclasses to inherit backend functionality."""

import os
import typing

from .. import parameters

from . import piping
from . import rendering
from . import unflattening
from . import viewing

__all__ = ['Render', 'Pipe', 'Unflatten', 'View']


class Render(parameters.Parameters):
    """Parameters for calling and calling ``graphviz.render()``."""

    def _get_render_parameters(self,
                               outfile: typing.Union[os.PathLike, str, None] = None,
                               raise_if_result_exists: bool = False,
                               overwrite_source: bool = False,
                               **kwargs):
        kwargs = self._get_parameters(**kwargs)
        kwargs.update(outfile=outfile,
                      raise_if_result_exists=raise_if_result_exists,
                      overwrite_filepath=overwrite_source)
        return [kwargs.pop('engine'), kwargs.pop('format')], kwargs

    @property
    def _render(_):  # noqa: N805
        """Simplify ``._render()`` mocking."""
        return rendering.render


class Pipe(parameters.Parameters):
    """Parameters for calling and calling ``graphviz.pipe()``."""

    _get_format = staticmethod(rendering.get_format)

    _get_filepath = staticmethod(rendering.get_filepath)

    def _get_pipe_parameters(self, **kwargs):
        kwargs = self._get_parameters(**kwargs)
        return [kwargs.pop('engine'), kwargs.pop('format')], kwargs

    @property
    def _pipe_lines(_):  # noqa: N805
        """Simplify ``._pipe_lines()`` mocking."""
        return piping.pipe_lines

    @property
    def _pipe_lines_string(_):  # noqa: N805
        """Simplify ``._pipe_lines_string()`` mocking."""
        return piping.pipe_lines_string


class Unflatten:

    @property
    def _unflatten(_):  # noqa: N805
        """Simplify ``._unflatten mocking."""
        return unflattening.unflatten


class View:
    """Open filepath with its default viewing application
        (platform-specific)."""

    _view_darwin = staticmethod(viewing.view_darwin)

    _view_freebsd = staticmethod(viewing.view_unixoid)

    _view_linux = staticmethod(viewing.view_unixoid)

    _view_windows = staticmethod(viewing.view_windows)
