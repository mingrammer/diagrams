"""Quote strings to be valid DOT identifiers, assemble quoted attribute lists."""

import functools
import re
import typing
import warnings

from . import _tools
from . import exceptions

__all__ = ['quote', 'quote_edge',
           'a_list', 'attr_list',
           'escape', 'nohtml']

# https://www.graphviz.org/doc/info/lang.html
# https://www.graphviz.org/doc/info/attrs.html#k:escString

HTML_STRING = re.compile(r'<.*>$', re.DOTALL)

ID = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*|-?(\.[0-9]+|[0-9]+(\.[0-9]*)?))$')

KEYWORDS = {'node', 'edge', 'graph', 'digraph', 'subgraph', 'strict'}

COMPASS = {'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', 'c', '_'}  # TODO

FINAL_ODD_BACKSLASHES = re.compile(r'(?<!\\)(?:\\{2})*\\$')

QUOTE_WITH_OPTIONAL_BACKSLASHES = re.compile(r'''
                                            (?P<escaped_backslashes>(?:\\{2})*)
                                            \\?  # treat \" same as "
                                            (?P<literal_quote>")
                                            ''', flags=re.VERBOSE)

ESCAPE_UNESCAPED_QUOTES = functools.partial(QUOTE_WITH_OPTIONAL_BACKSLASHES.sub,
                                            r'\g<escaped_backslashes>'
                                            r'\\'
                                            r'\g<literal_quote>')


@_tools.deprecate_positional_args(supported_number=1)
def quote(identifier: str,
          is_html_string=HTML_STRING.match,
          is_valid_id=ID.match,
          dot_keywords=KEYWORDS,
          endswith_odd_number_of_backslashes=FINAL_ODD_BACKSLASHES.search,
          escape_unescaped_quotes=ESCAPE_UNESCAPED_QUOTES) -> str:
    r"""Return DOT identifier from string, quote if needed.

    >>> quote('')  # doctest: +NO_EXE
    '""'

    >>> quote('spam')
    'spam'

    >>> quote('spam spam')
    '"spam spam"'

    >>> quote('-4.2')
    '-4.2'

    >>> quote('.42')
    '.42'

    >>> quote('<<b>spam</b>>')
    '<<b>spam</b>>'

    >>> quote(nohtml('<>'))
    '"<>"'

    >>> print(quote('"'))
    "\""

    >>> print(quote('\\"'))
    "\""

    >>> print(quote('\\\\"'))
    "\\\""

    >>> print(quote('\\\\\\"'))
    "\\\""
    """
    if is_html_string(identifier) and not isinstance(identifier, NoHtml):
        pass
    elif not is_valid_id(identifier) or identifier.lower() in dot_keywords:
        if endswith_odd_number_of_backslashes(identifier):
            warnings.warn('expect syntax error scanning invalid quoted string:'
                          f' {identifier!r}',
                          category=exceptions.DotSyntaxWarning)
        return f'"{escape_unescaped_quotes(identifier)}"'
    return identifier


def quote_edge(identifier: str) -> str:
    """Return DOT edge statement node_id from string, quote if needed.

    >>> quote_edge('spam')  # doctest: +NO_EXE
    'spam'

    >>> quote_edge('spam spam:eggs eggs')
    '"spam spam":"eggs eggs"'

    >>> quote_edge('spam:eggs:s')
    'spam:eggs:s'
    """
    node, _, rest = identifier.partition(':')
    parts = [quote(node)]
    if rest:
        port, _, compass = rest.partition(':')
        parts.append(quote(port))
        if compass:
            parts.append(compass)
    return ':'.join(parts)


@_tools.deprecate_positional_args(supported_number=1)
def a_list(label: typing.Optional[str] = None,
           kwargs=None, attributes=None) -> str:
    """Return assembled DOT a_list string.

    >>> a_list('spam', kwargs={'spam': None, 'ham': 'ham ham', 'eggs': ''})  # doctest: +NO_EXE
    'label=spam eggs="" ham="ham ham"'
    """
    result = [f'label={quote(label)}'] if label is not None else []
    if kwargs:
        result += [f'{quote(k)}={quote(v)}'
                   for k, v in _tools.mapping_items(kwargs) if v is not None]
    if attributes:
        if hasattr(attributes, 'items'):
            attributes = _tools.mapping_items(attributes)
        result += [f'{quote(k)}={quote(v)}'
                   for k, v in attributes if v is not None]
    return ' '.join(result)


@_tools.deprecate_positional_args(supported_number=1)
def attr_list(label: typing.Optional[str] = None,
              kwargs=None, attributes=None) -> str:
    """Return assembled DOT attribute list string.

    Sorts ``kwargs`` and ``attributes`` if they are plain dicts
    (to avoid unpredictable order from hash randomization in Python < 3.7).

    >>> attr_list()  # doctest: +NO_EXE
    ''

    >>> attr_list('spam spam', kwargs={'eggs': 'eggs', 'ham': 'ham ham'})
    ' [label="spam spam" eggs=eggs ham="ham ham"]'

    >>> attr_list(kwargs={'spam': None, 'eggs': ''})
    ' [eggs=""]'
    """
    content = a_list(label, kwargs=kwargs, attributes=attributes)
    if not content:
        return ''
    return f' [{content}]'


class Quote:
    """Quote strings to be valid DOT identifiers, assemble quoted attribute lists."""

    _quote = staticmethod(quote)
    _quote_edge = staticmethod(quote_edge)

    _a_list = staticmethod(a_list)
    _attr_list = staticmethod(attr_list)


def escape(s: str) -> str:
    r"""Return string disabling special meaning of backslashes and ``'<...>'``.

    Args:
        s: String in which backslashes and ``'<...>'``
            should be treated as literal.

    Returns:
        Escaped string subclass instance.

    Raises:
        TypeError: If ``s`` is not a ``str``.

    Example:
        >>> import graphviz  # doctest: +NO_EXE
        >>> print(graphviz.escape(r'\l'))
        \\l

    See also:
        Upstream documentation:
        https://www.graphviz.org/doc/info/attrs.html#k:escString
    """
    return nohtml(s.replace('\\', '\\\\'))


class NoHtml(str):
    """String subclass that does not treat ``'<...>'`` as DOT HTML string."""

    __slots__ = ()


def nohtml(s: str) -> str:
    """Return string not treating ``'<...>'`` as DOT HTML string in quoting.

    Args:
        s: String in which leading ``'<'`` and trailing ``'>'``
            should be treated as literal.

    Returns:
        String subclass instance.

    Raises:
        TypeError: If ``s`` is not a ``str``.

    Example:
        >>> import graphviz  # doctest: +NO_EXE
        >>> g = graphviz.Graph()
        >>> g.node(graphviz.nohtml('<>-*-<>'))
        >>> print(g.source)  # doctest: +NORMALIZE_WHITESPACE
        graph {
            "<>-*-<>"
        }
    """
    return NoHtml(s)
