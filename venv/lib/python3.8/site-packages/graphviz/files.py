# files.py - save, render, view

"""Save DOT code objects, render with Graphviz dot, and open in viewer."""

import os
import io
import codecs
import locale
import logging

from ._compat import text_type

from . import backend
from . import tools

__all__ = ['File', 'Source']

ENCODING = 'utf-8'


log = logging.getLogger(__name__)


class Base(object):

    _format = 'pdf'
    _engine = 'dot'
    _encoding = ENCODING

    @property
    def format(self):
        """The output format used for rendering (``'pdf'``, ``'png'``, ...)."""
        return self._format

    @format.setter
    def format(self, format):
        format = format.lower()
        if format not in backend.FORMATS:
            raise ValueError('unknown format: %r' % format)
        self._format = format

    @property
    def engine(self):
        """The layout commmand used for rendering (``'dot'``, ``'neato'``, ...)."""
        return self._engine

    @engine.setter
    def engine(self, engine):
        engine = engine.lower()
        if engine not in backend.ENGINES:
            raise ValueError('unknown engine: %r' % engine)
        self._engine = engine

    @property
    def encoding(self):
        """The encoding for the saved source file."""
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        if encoding is None:
            encoding = locale.getpreferredencoding()
        codecs.lookup(encoding)  # raise early
        self._encoding = encoding

    def copy(self):
        """Return a copied instance of the object.

        Returns:
            An independent copy of the current object.
        """
        kwargs = self._kwargs()
        return self.__class__(**kwargs)

    def _kwargs(self):
        ns = self.__dict__
        return {a[1:]: ns[a] for a in ('_format', '_engine', '_encoding')
                if a in ns}


class File(Base):

    directory = ''

    _default_extension = 'gv'

    def __init__(self, filename=None, directory=None,
                 format=None, engine=None, encoding=ENCODING):
        if filename is None:
            name = getattr(self, 'name', None) or self.__class__.__name__
            filename = '%s.%s' % (name, self._default_extension)
        self.filename = filename

        if directory is not None:
            self.directory = directory

        if format is not None:
            self.format = format

        if engine is not None:
            self.engine = engine

        self.encoding = encoding

    def _kwargs(self):
        result = super(File, self)._kwargs()
        result['filename'] = self.filename
        if 'directory' in self.__dict__:
            result['directory'] = self.directory
        return result

    def _repr_svg_(self):
        return self.pipe(format='svg').decode(self._encoding)

    def pipe(self, format=None, renderer=None, formatter=None, quiet=False):
        """Return the source piped through the Graphviz layout command.

        Args:
            format: The output format used for rendering (``'pdf'``, ``'png'``, etc.).
            renderer: The output renderer used for rendering (``'cairo'``, ``'gd'``, ...).
            formatter: The output formatter used for rendering (``'cairo'``, ``'gd'``, ...).
            quiet (bool): Suppress ``stderr`` output from the layout subprocess.
        Returns:
            Binary (encoded) stdout of the layout command.
        Raises:
            ValueError: If ``format``, ``renderer``, or ``formatter`` are not known.
            graphviz.RequiredArgumentError: If ``formatter`` is given but ``renderer`` is None.
            graphviz.ExecutableNotFound: If the Graphviz executable is not found.
            subprocess.CalledProcessError: If the exit status is non-zero.
        """
        if format is None:
            format = self._format

        data = text_type(self.source).encode(self._encoding)

        out = backend.pipe(self._engine, format, data,
                           renderer=renderer, formatter=formatter,
                           quiet=quiet)

        return out

    @property
    def filepath(self):
        return os.path.join(self.directory, self.filename)

    def save(self, filename=None, directory=None):
        """Save the DOT source to file. Ensure the file ends with a newline.

        Args:
            filename: Filename for saving the source (defaults to ``name`` + ``'.gv'``)
            directory: (Sub)directory for source saving and rendering.
        Returns:
            The (possibly relative) path of the saved source file.
        """
        if filename is not None:
            self.filename = filename
        if directory is not None:
            self.directory = directory

        filepath = self.filepath
        tools.mkdirs(filepath)

        data = text_type(self.source)

        log.debug('write %d bytes to %r', len(data), filepath)
        with io.open(filepath, 'w', encoding=self.encoding) as fd:
            fd.write(data)
            if not data.endswith(u'\n'):
                fd.write(u'\n')

        return filepath

    def render(self, filename=None, directory=None, view=False, cleanup=False,
               format=None, renderer=None, formatter=None,
               quiet=False, quiet_view=False):
        """Save the source to file and render with the Graphviz engine.

        Args:
            filename: Filename for saving the source (defaults to ``name`` + ``'.gv'``)
            directory: (Sub)directory for source saving and rendering.
            view (bool): Open the rendered result with the default application.
            cleanup (bool): Delete the source file after rendering.
            format: The output format used for rendering (``'pdf'``, ``'png'``, etc.).
            renderer: The output renderer used for rendering (``'cairo'``, ``'gd'``, ...).
            formatter: The output formatter used for rendering (``'cairo'``, ``'gd'``, ...).
            quiet (bool): Suppress ``stderr`` output from the layout subprocess.
            quiet_view (bool): Suppress ``stderr`` output from the viewer process
                               (implies ``view=True``, ineffective on Windows).
        Returns:
            The (possibly relative) path of the rendered file.
        Raises:
            ValueError: If ``format``, ``renderer``, or ``formatter`` are not known.
            graphviz.RequiredArgumentError: If ``formatter`` is given but ``renderer`` is None.
            graphviz.ExecutableNotFound: If the Graphviz executable is not found.
            subprocess.CalledProcessError: If the exit status is non-zero.
            RuntimeError: If viewer opening is requested but not supported.

        The layout command is started from the directory of ``filepath``, so that
        references to external files (e.g. ``[image=...]``) can be given as paths
        relative to the DOT source file.
        """
        filepath = self.save(filename, directory)

        if format is None:
            format = self._format

        rendered = backend.render(self._engine, format, filepath,
                                  renderer=renderer, formatter=formatter,
                                  quiet=quiet)

        if cleanup:
            log.debug('delete %r', filepath)
            os.remove(filepath)

        if quiet_view or view:
            self._view(rendered, self._format, quiet_view)

        return rendered

    def view(self, filename=None, directory=None, cleanup=False,
             quiet=False, quiet_view=False):
        """Save the source to file, open the rendered result in a viewer.

        Args:
            filename: Filename for saving the source (defaults to ``name`` + ``'.gv'``)
            directory: (Sub)directory for source saving and rendering.
            cleanup (bool): Delete the source file after rendering.
            quiet (bool): Suppress ``stderr`` output from the layout subprocess.
            quiet_view (bool): Suppress ``stderr`` output from the viewer process
                               (ineffective on Windows).
        Returns:
            The (possibly relative) path of the rendered file.
        Raises:
            graphviz.ExecutableNotFound: If the Graphviz executable is not found.
            subprocess.CalledProcessError: If the exit status is non-zero.
            RuntimeError: If opening the viewer is not supported.

        Short-cut method for calling :meth:`.render` with ``view=True``.
        """
        return self.render(filename=filename, directory=directory,
                           view=True, cleanup=cleanup,
                           quiet=quiet, quiet_view=quiet_view)

    def _view(self, filepath, format, quiet):
        """Start the right viewer based on file format and platform."""
        methodnames = [
            '_view_%s_%s' % (format, backend.PLATFORM),
            '_view_%s' % backend.PLATFORM,
        ]
        for name in methodnames:
            view_method = getattr(self, name, None)
            if view_method is not None:
                break
        else:
            raise RuntimeError('%r has no built-in viewer support for %r'
                               ' on %r platform' % (self.__class__, format,
                                                    backend.PLATFORM))
        view_method(filepath, quiet)

    _view_darwin = staticmethod(backend.view.darwin)
    _view_freebsd = staticmethod(backend.view.freebsd)
    _view_linux = staticmethod(backend.view.linux)
    _view_windows = staticmethod(backend.view.windows)


class Source(File):
    """Verbatim DOT source code string to be rendered by Graphviz.

    Args:
        source: The verbatim DOT source code string.
        filename: Filename for saving the source (defaults to ``'Source.gv'``).
        directory: (Sub)directory for source saving and rendering.
        format: Rendering output format (``'pdf'``, ``'png'``, ...).
        engine: Layout command used (``'dot'``, ``'neato'``, ...).
        encoding: Encoding for saving the source.

    Note:
        All parameters except ``source`` are optional. All of them can be changed
        under their corresponding attribute name after instance creation.
    """

    @classmethod
    def from_file(cls, filename, directory=None,
                  format=None, engine=None, encoding=ENCODING):
        """Return an instance with the source string read from the given file.

        Args:
            filename: Filename for loading/saving the source.
            directory: (Sub)directory for source loading/saving and rendering.
            format: Rendering output format (``'pdf'``, ``'png'``, ...).
            engine: Layout command used (``'dot'``, ``'neato'``, ...).
            encoding: Encoding for loading/saving the source.
        """
        filepath = os.path.join(directory or '', filename)
        if encoding is None:
            encoding = locale.getpreferredencoding()
        log.debug('read %r with encoding %r', filepath, encoding)
        with io.open(filepath, encoding=encoding) as fd:
            source = fd.read()
        return cls(source, filename, directory, format, engine, encoding)

    def __init__(self, source, filename=None, directory=None,
                 format=None, engine=None, encoding=ENCODING):
        super(Source, self).__init__(filename, directory,
                                     format, engine, encoding)
        self.source = source  #: The verbatim DOT source code string.

    def _kwargs(self):
        result = super(Source, self)._kwargs()
        result['source'] = self.source
        return result
