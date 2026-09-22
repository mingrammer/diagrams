"""Save DOT source lines to a file."""

import logging
import os
import typing

from . import _defaults
from . import _tools
from . import base
from . import encoding

__all__ = ['Save']

log = logging.getLogger(__name__)


class Save(encoding.Encoding, base.Base):
    """Save DOT source lines to file."""

    directory: typing.Union[str, bytes] = ''

    _default_extension = _defaults.DEFAULT_SOURCE_EXTENSION

    _mkdirs = staticmethod(_tools.mkdirs)

    def __init__(self, *,
                 filename: typing.Union[os.PathLike, str],
                 directory: typing.Union[os.PathLike, str, None] = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)

        if filename is None:
            filename = f'{self.__class__.__name__}.{self._default_extension}'

        self.filename = os.fspath(filename)
        """str: Target file name for saving the DOT source file."""

        if directory is not None:
            self.directory = os.fspath(directory)

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        assert 'directory' not in kwargs
        if 'directory' in self.__dict__:
            kwargs['directory'] = self.directory
        return super()._copy_kwargs(filename=self.filename, **kwargs)

    @property
    def filepath(self) -> str:
        """The target path for saving the DOT source file."""
        return os.path.join(self.directory, self.filename)

    @_tools.deprecate_positional_args(supported_number=2)
    def save(self, filename: typing.Union[os.PathLike, str, None] = None,
             directory: typing.Union[os.PathLike, str, None] = None, *,
             skip_existing: typing.Optional[bool] = False) -> str:
        """Save the DOT source to file. Ensure the file ends with a newline.

        Args:
            filename: Filename for saving the source (defaults to ``name`` + ``'.gv'``)
            directory: (Sub)directory for source saving and rendering.
            skip_existing: Skip write if file exists (default: ``False``).

        Returns:
            The (possibly relative) path of the saved source file.
        """
        if filename is not None:
            self.filename = filename
        if directory is not None:
            self.directory = directory

        filepath = self.filepath
        if skip_existing and os.path.exists(filepath):
            return filepath

        self._mkdirs(filepath)

        log.debug('write lines to %r', filepath)
        with open(filepath, 'w', encoding=self.encoding) as fd:
            for uline in self:
                fd.write(uline)

        return filepath
