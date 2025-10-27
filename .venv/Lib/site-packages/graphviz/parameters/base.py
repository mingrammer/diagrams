"""Rendering parameter handling."""

from .. import copying

__all__ = ['ParameterBase']


class ParameterBase(copying.CopyBase):
    """Rendering parameter."""

    def _getattr_from_dict(self, attrname: str, *, default=None):
        """Return self.attrname if attrname is in the instance dictionary
            (as oposed to on the type)."""
        if attrname in self.__dict__:
            return getattr(self, attrname)
        return default
