"""Rendering formatter parameter handling."""

import typing

from . import base

__all__ = ['FORMATTERS', 'verify_formatter', 'Formatter']

FORMATTERS = {'cairo',
              'core',
              'gd',
              'gdiplus',
              'gdwbmp',
              'xlib'}

REQUIRED = False


def verify_formatter(formatter: typing.Optional[str], *,
                     required: bool = REQUIRED) -> None:
    if formatter is None:
        if required:
            raise ValueError('missing formatter')
    elif formatter.lower() not in FORMATTERS:
        raise ValueError(f'unknown formatter: {formatter!r}'
                         f' (must be None or one of {sorted(FORMATTERS)})')


class Formatter(base.ParameterBase):
    """Rendering engine parameter (no default)."""

    _formatter = None

    _verify_formatter = staticmethod(verify_formatter)

    def __init__(self, *, formatter: typing.Optional[str] = None, **kwargs) -> None:
        super().__init__(**kwargs)

        self.formatter = formatter

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        formatter = self._getattr_from_dict('_formatter')
        if formatter is not None:
            kwargs['formatter'] = formatter
        return super()._copy_kwargs(**kwargs)

    @property
    def formatter(self) -> typing.Optional[str]:
        """The output formatter used for rendering
            (``'cairo'``, ``'gd'``, ...)."""
        return self._formatter

    @formatter.setter
    def formatter(self, formatter: typing.Optional[str]) -> None:
        if formatter is None:
            self.__dict__.pop('_formatter', None)
        else:
            formatter = formatter.lower()
            self._verify_formatter(formatter)
            self._formatter = formatter
