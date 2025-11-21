"""Rendering engine parameter handling."""

import typing

from . import base

__all__ = ['ENGINES', 'verify_engine', 'Engine']

ENGINES = {'dot',  # https://www.graphviz.org/pdf/dot.1.pdf
           'neato',
           'twopi',
           'circo',
           'fdp',
           'sfdp',
           'patchwork',
           'osage'}

DEFAULT_ENGINE = 'dot'

REQUIRED = True


def verify_engine(engine: str, *, required: bool = REQUIRED) -> None:
    if engine is None:
        if required:
            raise ValueError('missing engine')
    elif engine.lower() not in ENGINES:
        raise ValueError(f'unknown engine: {engine!r}'
                         f' (must be one of {sorted(ENGINES)})')


class Engine(base.ParameterBase):
    """Rendering engine parameter with ``'dot''`` default."""

    _engine = DEFAULT_ENGINE

    _verify_engine = staticmethod(verify_engine)

    def __init__(self, *, engine: typing.Optional[str] = None, **kwargs) -> None:
        super().__init__(**kwargs)

        if engine is not None:
            self.engine = engine

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        engine = self._getattr_from_dict('_engine')
        if engine is not None:
            kwargs['engine'] = engine
        return super()._copy_kwargs(**kwargs)

    @property
    def engine(self) -> str:
        """The layout engine used for rendering
            (``'dot'``, ``'neato'``, ...)."""
        return self._engine

    @engine.setter
    def engine(self, engine: str) -> None:
        engine = engine.lower()
        self._verify_engine(engine)
        self._engine = engine
