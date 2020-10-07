import types
from ast import literal_eval
from itertools import chain
from itertools import islice

from . import nodes
from ._compat import text_type
from .compiler import CodeGenerator
from .compiler import has_safe_repr
from .environment import Environment
from .environment import Template


def native_concat(nodes, preserve_quotes=True):
    """Return a native Python type from the list of compiled nodes. If
    the result is a single node, its value is returned. Otherwise, the
    nodes are concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise,
    the string is returned.

    :param nodes: Iterable of nodes to concatenate.
    :param preserve_quotes: Whether to re-wrap literal strings with
        quotes, to preserve quotes around expressions for later parsing.
        Should be ``False`` in :meth:`NativeEnvironment.render`.
    """
    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        raw = head[0]
    else:
        if isinstance(nodes, types.GeneratorType):
            nodes = chain(head, nodes)
        raw = u"".join([text_type(v) for v in nodes])

    try:
        literal = literal_eval(raw)
    except (ValueError, SyntaxError, MemoryError):
        return raw

    # If literal_eval returned a string, re-wrap with the original
    # quote character to avoid dropping quotes between expression nodes.
    # Without this, "'{{ a }}', '{{ b }}'" results in "a, b", but should
    # be ('a', 'b').
    if preserve_quotes and isinstance(literal, str):
        return "{quote}{}{quote}".format(literal, quote=raw[0])

    return literal


class NativeCodeGenerator(CodeGenerator):
    """A code generator which renders Python types by not adding
    ``to_string()`` around output nodes, and using :func:`native_concat`
    to convert complex strings back to Python types if possible.
    """

    @staticmethod
    def _default_finalize(value):
        return value

    def _output_const_repr(self, group):
        return repr(native_concat(group))

    def _output_child_to_const(self, node, frame, finalize):
        const = node.as_const(frame.eval_ctx)

        if not has_safe_repr(const):
            raise nodes.Impossible()

        if isinstance(node, nodes.TemplateData):
            return const

        return finalize.const(const)

    def _output_child_pre(self, node, frame, finalize):
        if finalize.src is not None:
            self.write(finalize.src)

    def _output_child_post(self, node, frame, finalize):
        if finalize.src is not None:
            self.write(")")


class NativeEnvironment(Environment):
    """An environment that renders templates to native Python types."""

    code_generator_class = NativeCodeGenerator


class NativeTemplate(Template):
    environment_class = NativeEnvironment

    def render(self, *args, **kwargs):
        """Render the template to produce a native Python type. If the
        result is a single node, its value is returned. Otherwise, the
        nodes are concatenated as strings. If the result can be parsed
        with :func:`ast.literal_eval`, the parsed value is returned.
        Otherwise, the string is returned.
        """
        vars = dict(*args, **kwargs)
        try:
            return native_concat(
                self.root_render_func(self.new_context(vars)), preserve_quotes=False
            )
        except Exception:
            return self.environment.handle_exception()


NativeEnvironment.template_class = NativeTemplate
