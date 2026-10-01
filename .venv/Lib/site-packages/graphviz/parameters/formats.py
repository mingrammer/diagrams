"""Rendering format parameter handling."""

import typing

from . import base

__all__ = ['FORMATS', 'verify_format', 'Format']

FORMATS = {'bmp',  # https://graphviz.org/docs/outputs/
           'canon', 'dot', 'gv', 'xdot', 'xdot1.2', 'xdot1.4',
           'cgimage',
           'cmap',
           'eps',
           'exr',
           'fig',
           'gd', 'gd2',
           'gif',
           'gtk',
           'ico',
           'imap', 'cmapx',
           'imap_np', 'cmapx_np',
           'ismap',
           'jp2',
           'jpg', 'jpeg', 'jpe',
           'json', 'json0', 'dot_json', 'xdot_json',  # Graphviz 2.40
           'pct', 'pict',
           'pdf',
           'pic',
           'plain', 'plain-ext',
           'png',
           'pov',
           'ps',
           'ps2',
           'psd',
           'sgi',
           'svg', 'svgz',
           'tga',
           'tif', 'tiff',
           'tk',
           'vml', 'vmlz',
           'vrml',
           'wbmp',
           'webp',
           'xlib', 'x11'}

DEFAULT_FORMAT = 'pdf'

REQUIRED = True


def verify_format(format: str, *, required: bool = REQUIRED) -> None:
    if format is None:
        if required:
            raise ValueError('missing format')
    elif format.lower() not in FORMATS:
        raise ValueError(f'unknown format: {format!r}'
                         f' (must be one of {sorted(FORMATS)})')


class Format(base.ParameterBase):
    """Rendering format parameter with ``'pdf'`` default."""

    _format = DEFAULT_FORMAT

    _verify_format = staticmethod(verify_format)

    def __init__(self, *, format: typing.Optional[str] = None, **kwargs) -> None:
        super().__init__(**kwargs)

        if format is not None:
            self.format = format

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        format = self._getattr_from_dict('_format')
        if format is not None:
            kwargs['format'] = format
        return super()._copy_kwargs(**kwargs)

    @property
    def format(self) -> str:
        """The output format used for rendering
            (``'pdf'``, ``'png'``, ...)."""
        return self._format

    @format.setter
    def format(self, format: str) -> None:
        format = format.lower()
        self._verify_format(format)
        self._format = format
