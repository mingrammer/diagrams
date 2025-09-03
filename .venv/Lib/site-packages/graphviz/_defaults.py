"""Set package-wide default parameters and IPython/Jupyter display format."""

__all_ = ['DEFAULT_SOURCE_EXTENSION',
          'set_default_engine', 'set_default_format', 'set_jupyter_format']

DEFAULT_SOURCE_EXTENSION = 'gv'


def set_default_engine(engine: str) -> str:
    """Change the default ``engine`` and return the old default value.

    Args:
        engine: new default ``engine``
            used by all present and newly created instances
            without explicitly set ``engine``
            (``'dot'``, ``'neato'``, ...).

    Returns:
        The old default value used for ``engine``.
    """
    from . import parameters

    parameters.verify_engine(engine)

    old_default_engine = parameters.Parameters._engine
    parameters.Parameters._engine = engine
    return old_default_engine


def set_default_format(format: str) -> str:
    """Change the default ``format`` and return the old default value.

    Args:
        format: new default ``format``
            used by all present and newly created instances
            without explicitly set ``format``
            (``'pdf'``, ``'png'``, ...).

    Returns:
        The old default value used for ``format``.
    """
    from . import parameters

    parameters.verify_format(format)

    old_default_format = parameters.Parameters._format
    parameters.Parameters._format = format
    return old_default_format


def set_jupyter_format(jupyter_format: str) -> str:
    """Change the default mimetype format for ``_repr_mimebundle_()`` and return the old value.

    Args:
        jupyter_format: new default IPython/Jupyter display format
            used by all present and newly created instances
            (``'svg'``, ``'png'``, ...).

    Returns:
        The old default value used for IPython/Jupyter display format.
    """
    from . import jupyter_integration

    mimetype = jupyter_integration.get_jupyter_format_mimetype(jupyter_format)

    old_mimetype = jupyter_integration.JupyterIntegration._jupyter_mimetype
    old_format = jupyter_integration.get_jupyter_mimetype_format(old_mimetype)

    jupyter_integration.JupyterIntegration._jupyter_mimetype = mimetype
    return old_format
