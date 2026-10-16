"""Save DOT code objects, render with Graphviz ``dot``, and open in viewer."""

import logging
import os
import pathlib
import typing

from . import _tools
from . import backend
from . import saving

__all__ = ['Render']


log = logging.getLogger(__name__)


class Render(saving.Save, backend.Render, backend.View):
    """Write source lines to file and render with Graphviz."""

    @_tools.deprecate_positional_args(supported_number=2)
    def render(self,
               filename: typing.Union[os.PathLike, str, None] = None,
               directory: typing.Union[os.PathLike, str, None] = None,
               view: bool = False,
               cleanup: bool = False,
               format: typing.Optional[str] = None,
               renderer: typing.Optional[str] = None,
               formatter: typing.Optional[str] = None,
               neato_no_op: typing.Union[bool, int, None] = None,
               quiet: bool = False,
               quiet_view: bool = False, *,
               outfile: typing.Union[os.PathLike, str, None] = None,
               engine: typing.Optional[str] = None,
               raise_if_result_exists: bool = False,
               overwrite_source: bool = False) -> str:
        r"""Save the source to file and render with the Graphviz engine.

        Args:
            filename: Filename for saving the source
                (defaults to ``name`` + ``'.gv'``).s
            directory: (Sub)directory for source saving and rendering.
            view (bool): Open the rendered result
                with the default application.
            cleanup (bool): Delete the source file
                after successful rendering.
            format: The output format used for rendering
                (``'pdf'``, ``'png'``, etc.).
            renderer: The output renderer used for rendering
                (``'cairo'``, ``'gd'``, ...).
            formatter: The output formatter used for rendering
                (``'cairo'``, ``'gd'``, ...).
            neato_no_op: Neato layout engine no-op flag.
            quiet (bool): Suppress ``stderr`` output
                from the layout subprocess.
            quiet_view (bool): Suppress ``stderr`` output
                from the viewer process
                (implies ``view=True``, ineffective on Windows platform).
            outfile: Path for the rendered output file.
            engine: Layout engine for rendering
                (``'dot'``, ``'neato'``, ...).
            raise_if_result_exists: Raise :exc:`graphviz.FileExistsError`
                if the result file exists.
            overwrite_source: Allow ``dot`` to write to the file it reads from.
                Incompatible with ``raise_if_result_exists``.

        Returns:
            The (possibly relative) path of the rendered file.

        Raises:
            ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
                are unknown.
            graphviz.RequiredArgumentError: If ``formatter`` is given
                but ``renderer`` is None.
            ValueError: If ``outfile`` is the same file as the source file
                unless ``overwite_source=True``.
            graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
                is not found.
            graphviz.CalledProcessError: If the returncode (exit status)
                of the rendering ``dot`` subprocess is non-zero.
            RuntimeError: If viewer opening is requested but not supported.

        Example:
            >>> doctest_mark_exe()
            >>> import graphviz
            >>> dot = graphviz.Graph(name='spam', directory='doctest-output')
            >>> dot.render(format='png').replace('\\', '/')
            'doctest-output/spam.gv.png'
            >>> dot.render(outfile='spam.svg').replace('\\', '/')
            'doctest-output/spam.svg'

        Note:
            The layout command is started from the directory of ``filepath``,
            so that references to external files
            (e.g. ``[image=images/camelot.png]``)
            can be given as paths relative to the DOT source file.
        """
        outfile = _tools.promote_pathlike(outfile)
        if outfile is not None:
            format = self._get_format(outfile, format=format)
            if directory is None:
                outfile = pathlib.Path(self.directory, outfile)

        args, kwargs = self._get_render_parameters(engine=engine,
                                                   format=format,
                                                   renderer=renderer,
                                                   formatter=formatter,
                                                   neato_no_op=neato_no_op,
                                                   quiet=quiet,
                                                   outfile=outfile,
                                                   raise_if_result_exists=raise_if_result_exists,
                                                   overwrite_source=overwrite_source,
                                                   verify=True)

        if outfile is not None and filename is None:
            filename = self._get_filepath(outfile)

        filepath = self.save(filename, directory=directory, skip_existing=None)

        args.append(filepath)

        rendered = self._render(*args, **kwargs)

        if cleanup:
            log.debug('delete %r', filepath)
            os.remove(filepath)

        if quiet_view or view:
            self._view(rendered, format=self._format, quiet=quiet_view)

        return rendered

    def _view(self, filepath: typing.Union[os.PathLike, str], *,
              format: str, quiet: bool) -> None:
        """Start the right viewer based on file format and platform."""
        methodnames = [
            f'_view_{format}_{backend.viewing.PLATFORM}',
            f'_view_{backend.viewing.PLATFORM}',
        ]
        for name in methodnames:
            view_method = getattr(self, name, None)
            if view_method is not None:
                break
        else:
            raise RuntimeError(f'{self.__class__!r} has no built-in viewer'
                               f' support for {format!r}'
                               f' on {backend.viewing.PLATFORM!r} platform')
        view_method(filepath, quiet=quiet)

    @_tools.deprecate_positional_args(supported_number=2)
    def view(self,
             filename: typing.Union[os.PathLike, str, None] = None,
             directory: typing.Union[os.PathLike, str, None] = None,
             cleanup: bool = False,
             quiet: bool = False,
             quiet_view: bool = False) -> str:
        """Save the source to file, open the rendered result in a viewer.

        Convenience short-cut for running ``.render(view=True)``.

        Args:
            filename: Filename for saving the source
                (defaults to ``name`` + ``'.gv'``).
            directory: (Sub)directory for source saving and rendering.
            cleanup (bool): Delete the source file after successful rendering.
            quiet (bool): Suppress ``stderr`` output from the layout subprocess.
            quiet_view (bool): Suppress ``stderr`` output
                from the viewer process (ineffective on Windows).

        Returns:
            The (possibly relative) path of the rendered file.

        Raises:
            graphviz.ExecutableNotFound: If the Graphviz executable
                is not found.
            graphviz.CalledProcessError: If the exit status is non-zero.
            RuntimeError: If opening the viewer is not supported.

        Short-cut method for calling :meth:`.render` with ``view=True``.

        Note:
            There is no option to wait for the application to close,
            and no way to retrieve the application's exit status.
        """
        return self.render(filename=filename, directory=directory, view=True,
                           cleanup=cleanup, quiet=quiet, quiet_view=quiet_view)
