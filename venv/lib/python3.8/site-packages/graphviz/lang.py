# lang.py - dot language creation helpers

"""Quote strings to be valid DOT identifiers, assemble attribute lists."""

import re
import collections
import functools

from . import _compat

from . import tools

__all__ = ['quote', 'quote_edge', 'a_list', 'attr_list', 'escape', 'nohtml']

# https://www.graphviz.org/doc/info/lang.html
# https://www.graphviz.org/doc/info/attrs.html#k:escString

HTML_STRING = re.compile(r'<.*>$', re.DOTALL)

ID = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*|-?(\.[0-9]+|[0-9]+(\.[0-9]*)?))$')

KEYWORDS = {'node', 'edge', 'graph', 'digraph', 'subgraph', 'strict'}

COMPASS = {'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', 'c', '_'}  # TODO

ESCAPE_UNESCAPED_QUOTES = functools.partial(re.compile(r'(?!\\)"').sub, r'\\"')


def quote(identifier,
          is_html_string=HTML_STRING.match,
          is_valid_id=ID.match, dot_keywords=KEYWORDS,
          escape_unescaped_quotes=ESCAPE_UNESCAPED_QUOTES):
    r"""Return DOT identifier from string, quote if needed.

    >>> quote('')
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
    "\\""
    """
    if is_html_string(identifier) and not isinstance(identifier, NoHtml):
        pass
    elif not is_valid_id(identifier) or identifier.lower() in dot_keywords:
        return '"%s"' % escape_unescaped_quotes(identifier)
    return identifier


def quote_edge(identifier):
    """Return DOT edge statement node_id from string, quote if needed.

    >>> quote_edge('spam')
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


def a_list(label=None, kwargs=None, attributes=None):
    """Return assembled DOT a_list string.

    >>> a_list('spam', {'spam': None, 'ham': 'ham ham', 'eggs': ''})
    'label=spam eggs="" ham="ham ham"'
    """
    result = ['label=%s' % quote(label)] if label is not None else []
    if kwargs:
        items = ['%s=%s' % (quote(k), quote(v))
                 for k, v in tools.mapping_items(kwargs) if v is not None]
        result.extend(items)
    if attributes:
        if hasattr(attributes, 'items'):
            attributes = tools.mapping_items(attributes)
        items = ['%s=%s' % (quote(k), quote(v))
                 for k, v in attributes if v is not None]
        result.extend(items)
    return ' '.join(result)


def attr_list(label=None, kwargs=None, attributes=None):
    """Return assembled DOT attribute list string.

    Sorts ``kwargs`` and ``attributes`` if they are plain dicts (to avoid
    unpredictable order from hash randomization in Python 3 versions).

    >>> attr_list()
    ''

    >>> attr_list('spam spam', kwargs={'eggs': 'eggs', 'ham': 'ham ham'})
    ' [label="spam spam" eggs=eggs ham="ham ham"]'

    >>> attr_list(kwargs={'spam': None, 'eggs': ''})
    ' [eggs=""]'
    """
    content = a_list(label, kwargs, attributes)
    if not content:
        return ''
    return ' [%s]' % content


def escape(s):
    r"""Return ``s`` as literal disabling special meaning of backslashes and ``'<...>'``.

    see also https://www.graphviz.org/doc/info/attrs.html#k:escString

    Args:
        s: String in which backslashes and ``'<...>'`` should be treated as literal.
    Raises:
        TypeError: If ``s`` is not a ``str`` on Python 3, or a ``str``/``unicode`` on Python 2.

    >>> print(escape(r'\l'))
    \\l
    """
    return nohtml(s.replace('\\', '\\\\'))


class NoHtml(object):
    """Mixin for string subclasses disabling fall-through of ``'<...>'``."""

    __slots__ = ()

    _doc = "%s subclass that does not treat ``'<...>'`` as DOT HTML string."

    @classmethod
    def _subcls(cls, other):
        name = '%s_%s' % (cls.__name__, other.__name__)
        bases = (other, cls)
        ns = {'__doc__': cls._doc % other.__name__}
        return type(name, bases, ns)


NOHTML = collections.OrderedDict((c, NoHtml._subcls(c)) for c in _compat.string_classes)


def nohtml(s):
    """Return copy of ``s`` that will not treat ``'<...>'`` as DOT HTML string in quoting.

    Args:
        s: String in which leading ``'<'`` and trailing ``'>'`` should be treated as literal.
    Raises:
        TypeError: If ``s`` is not a ``str`` on Python 3, or a ``str``/``unicode`` on Python 2.

    >>> quote('<>-*-<>')
    '<>-*-<>'

    >>> quote(nohtml('<>-*-<>'))
    '"<>-*-<>"'
    """
    try:
        subcls = NOHTML[type(s)]
    except KeyError:
        raise TypeError('%r does not have one of the required types:'
                        ' %r' % (s, list(NOHTML)))
    return subcls(s)
