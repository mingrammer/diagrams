"""Render DOT source files with Graphviz ``dot``."""

import os
import pathlib
import typing
import warnings

from .._defaults import DEFAULT_SOURCE_EXTENSION
from .. import _tools
from .. import exceptions
from .. import parameters

from . import dot_command
from . import execute

__all__ = ['get_format', 'get_filepath', 'render']


def get_format(outfile: pathlib.Path, *, format: typing.Optional[str]) -> str:
    """Return format inferred from outfile suffix and/or given ``format``.

    Args:
        outfile: Path for the rendered output file.
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).

    Returns:
        The given ``format`` falling back to the inferred format.

    Warns:
        graphviz.UnknownSuffixWarning: If the suffix of ``outfile``
            is empty/unknown.
        graphviz.FormatSuffixMismatchWarning: If the suffix of ``outfile``
            does not match the given ``format``.
    """
    try:
        inferred_format = infer_format(outfile)
    except ValueError:
        if format is None:
            msg = ('cannot infer rendering format'
                   f' from suffix {outfile.suffix!r}'
                   f' of outfile: {os.fspath(outfile)!r}'
                   ' (provide format or outfile with a suffix'
                   f' from {get_supported_suffixes()!r})')
            raise exceptions.RequiredArgumentError(msg)

        warnings.warn(f'unknown outfile suffix {outfile.suffix!r}'
                      f' (expected: {"." + format!r})',
                      category=exceptions.UnknownSuffixWarning)
        return format
    else:
        assert inferred_format is not None
        if format is not None and format.lower() != inferred_format:
            warnings.warn(f'expected format {inferred_format!r} from outfile'
                          f' differs from given format: {format!r}',
                          category=exceptions.FormatSuffixMismatchWarning)
            return format

        return inferred_format


def get_supported_suffixes() -> typing.List[str]:
    """Return a sorted list of supported outfile suffixes for exception/warning messages.

    >>> get_supported_suffixes()  # doctest: +ELLIPSIS
    ['.bmp', ...]
    """
    return [f'.{format}' for format in get_supported_formats()]


def get_supported_formats() -> typing.List[str]:
    """Return a sorted list of supported formats for exception/warning messages.

    >>> get_supported_formats()  # doctest: +ELLIPSIS
    ['bmp', ...]
    """
    return sorted(parameters.FORMATS)


def infer_format(outfile: pathlib.Path) -> str:
    """Return format inferred from outfile suffix.

    Args:
        outfile: Path for the rendered output file.

    Returns:
        The inferred format.

    Raises:
        ValueError: If the suffix of ``outfile`` is empty/unknown.

    >>> infer_format(pathlib.Path('spam.pdf'))  # doctest: +NO_EXE
    'pdf'

    >>> infer_format(pathlib.Path('spam.gv.svg'))
    'svg'

    >>> infer_format(pathlib.Path('spam.PNG'))
    'png'

    >>> infer_format(pathlib.Path('spam'))
    Traceback (most recent call last):
        ...
    ValueError: cannot infer rendering format from outfile: 'spam' (missing suffix)

    >>> infer_format(pathlib.Path('spam.wav'))  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: cannot infer rendering format from suffix '.wav' of outfile: 'spam.wav'
    (unknown format: 'wav', provide outfile with a suffix from ['.bmp', ...])
    """
    if not outfile.suffix:
        raise ValueError('cannot infer rendering format from outfile:'
                         f' {os.fspath(outfile)!r} (missing suffix)')

    start, sep, format_ = outfile.suffix.partition('.')
    assert sep and not start, f"{outfile.suffix!r}.startswith('.')"
    format_ = format_.lower()

    try:
        parameters.verify_format(format_)
    except ValueError:
        raise ValueError('cannot infer rendering format'
                         f' from suffix {outfile.suffix!r}'
                         f' of outfile: {os.fspath(outfile)!r}'
                         f' (unknown format: {format_!r},'
                         ' provide outfile with a suffix'
                         f' from {get_supported_suffixes()!r})')
    return format_


def get_outfile(filepath: typing.Union[os.PathLike, str], *,
                format: str,
                renderer: typing.Optional[str] = None,
                formatter: typing.Optional[str] = None) -> pathlib.Path:
    """Return ``filepath`` + ``[[.formatter].renderer].format``.

    See also:
        https://www.graphviz.org/doc/info/command.html#-O
    """
    filepath = _tools.promote_pathlike(filepath)

    parameters.verify_format(format, required=True)
    parameters.verify_renderer(renderer, required=False)
    parameters.verify_formatter(formatter, required=False)

    suffix_args = (formatter, renderer, format)
    suffix = '.'.join(a for a in suffix_args if a is not None)
    return filepath.with_suffix(f'{filepath.suffix}.{suffix}')


def get_filepath(outfile: typing.Union[os.PathLike, str]) -> pathlib.Path:
    """Return ``outfile.with_suffix('.gv')``."""
    outfile = _tools.promote_pathlike(outfile)
    return outfile.with_suffix(f'.{DEFAULT_SOURCE_EXTENSION}')


@typing.overload
def render(engine: str,
           format: str,
           filepath: typing.Union[os.PathLike, str],
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           neato_no_op: typing.Union[bool, int, None] = ...,
           quiet: bool = ..., *,
           outfile: typing.Union[os.PathLike, str, None] = ...,
           raise_if_result_exists: bool = ...,
           overwrite_filepath: bool = ...) -> str:
    """Require ``format`` and ``filepath`` with default ``outfile=None``."""


@typing.overload
def render(engine: str,
           format: typing.Optional[str] = ...,
           filepath: typing.Union[os.PathLike, str, None] = ...,
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           neato_no_op: typing.Union[bool, int, None] = ...,
           quiet: bool = False, *,
           outfile: typing.Union[os.PathLike, str, None] = ...,
           raise_if_result_exists: bool = ...,
           overwrite_filepath: bool = ...) -> str:
    """Optional ``format`` and ``filepath`` with given ``outfile``."""


@typing.overload
def render(engine: str,
           format: typing.Optional[str] = ...,
           filepath: typing.Union[os.PathLike, str, None] = ...,
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           neato_no_op: typing.Union[bool, int, None] = ...,
           quiet: bool = False, *,
           outfile: typing.Union[os.PathLike, str, None] = ...,
           raise_if_result_exists: bool = ...,
           overwrite_filepath: bool = ...) -> str:
    """Required/optional ``format`` and ``filepath`` depending on ``outfile``."""


@_tools.deprecate_positional_args(supported_number=3)
def render(engine: str,
           format: typing.Optional[str] = None,
           filepath: typing.Union[os.PathLike, str, None] = None,
           renderer: typing.Optional[str] = None,
           formatter: typing.Optional[str] = None,
           neato_no_op: typing.Union[bool, int, None] = None,
           quiet: bool = False, *,
           outfile: typing.Union[os.PathLike, str, None] = None,
           raise_if_result_exists: bool = False,
           overwrite_filepath: bool = False) -> str:
    r"""Render file with ``engine`` into ``format`` and return result filename.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
            Can be omitted if an ``outfile`` with a known ``format`` is given,
            i.e. if ``outfile`` ends  with a known ``.{format}`` suffix.
        filepath: Path to the DOT source file to render.
            Can be omitted if ``outfile`` is given,
            in which case it defaults to ``outfile.with_suffix('.gv')``.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        neato_no_op: Neato layout engine no-op flag.
        quiet: Suppress ``stderr`` output from the layout subprocess.
        outfile: Path for the rendered output file.
        raise_if_result_exists: Raise :exc:`graphviz.FileExistsError`
            if the result file exists.
        overwrite_filepath: Allow ``dot`` to write to the file it reads from.
            Incompatible with ``raise_if_result_exists``.

    Returns:
        The (possibly relative) path of the rendered file.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``format`` or ``filepath`` are None
            unless ``outfile`` is given.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        ValueError: If ``outfile`` and ``filename`` are the same file
            unless ``overwite_filepath=True``.
        graphviz.ExecutableNotFound: If the Graphviz ``dot`` executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering ``dot`` subprocess is non-zero.
        graphviz.FileExistsError: If ``raise_if_exists``
            and the result file exists.

    Warns:
        graphviz.UnknownSuffixWarning: If the suffix of ``outfile``
            is empty or unknown.
        graphviz.FormatSuffixMismatchWarning: If the suffix of ``outfile``
            does not match the given ``format``.

    Example:
        >>> doctest_mark_exe()
        >>> import pathlib
        >>> import graphviz
        >>> assert pathlib.Path('doctest-output/spam.gv').write_text('graph { spam }') == 14
        >>> graphviz.render('dot', 'png', 'doctest-output/spam.gv').replace('\\', '/')
        'doctest-output/spam.gv.png'
        >>> graphviz.render('dot', filepath='doctest-output/spam.gv',
        ...                 outfile='doctest-output/spam.png').replace('\\', '/')
        'doctest-output/spam.png'
        >>> graphviz.render('dot', outfile='doctest-output/spam.pdf').replace('\\', '/')
        'doctest-output/spam.pdf'

    Note:
        The layout command is started from the directory of ``filepath``,
        so that references to external files
        (e.g. ``[image=images/camelot.png]``)
        can be given as paths relative to the DOT source file.

    See also:
        Upstream docs: https://www.graphviz.org/doc/info/command.html
    """
    if raise_if_result_exists and overwrite_filepath:
        raise ValueError('overwrite_filepath cannot be combined'
                         ' with raise_if_result_exists')

    filepath, outfile = map(_tools.promote_pathlike, (filepath, outfile))

    if outfile is not None:
        format = get_format(outfile, format=format)

        if filepath is None:
            filepath = get_filepath(outfile)

        if (not overwrite_filepath and outfile.name == filepath.name
            and outfile.resolve() == filepath.resolve()):  # noqa: E129
            raise ValueError(f'outfile {outfile.name!r} must be different'
                             f' from input file {filepath.name!r}'
                             ' (pass overwrite_filepath=True to override)')

        outfile_arg = (outfile.resolve() if outfile.parent != filepath.parent
                       else outfile.name)

        # https://www.graphviz.org/doc/info/command.html#-o
        args = ['-o', outfile_arg, filepath.name]
    elif filepath is None:
        raise exceptions.RequiredArgumentError('filepath: (required if outfile is not given,'
                                               f' got {filepath!r})')
    elif format is None:
        raise exceptions.RequiredArgumentError('format: (required if outfile is not given,'
                                               f' got {format!r})')
    else:
        outfile = get_outfile(filepath,
                              format=format,
                              renderer=renderer,
                              formatter=formatter)
        # https://www.graphviz.org/doc/info/command.html#-O
        args = ['-O', filepath.name]

    cmd = dot_command.command(engine, format,
                              renderer=renderer,
                              formatter=formatter,
                              neato_no_op=neato_no_op)

    if raise_if_result_exists and os.path.exists(outfile):
        raise exceptions.FileExistsError(f'output file exists: {os.fspath(outfile)!r}')

    cmd += args

    assert filepath is not None, 'work around pytype false alarm'

    execute.run_check(cmd,
                      cwd=filepath.parent if filepath.parent.parts else None,
                      quiet=quiet,
                      capture_output=True)

    return os.fspath(outfile)
