"""Create new instance copies with cooperative ``super()`` calls."""

__all__ = ['CopyBase']


class CopyBase:
    """Create new instance copies with cooperative ``super()`` calls."""

    def copy(self):
        """Return a copied instance of the object.

        Returns:
            An independent copy of the current object.
        """
        kwargs = self._copy_kwargs()
        return self.__class__(**kwargs)

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        return kwargs
