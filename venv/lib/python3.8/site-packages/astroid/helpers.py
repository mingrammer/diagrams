# Copyright (c) 2015-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""
Various helper utilities.
"""

import builtins as builtins_mod

from astroid import bases
from astroid import context as contextmod
from astroid import exceptions
from astroid import manager
from astroid import nodes
from astroid import raw_building
from astroid import scoped_nodes
from astroid import util


BUILTINS = builtins_mod.__name__


def _build_proxy_class(cls_name, builtins):
    proxy = raw_building.build_class(cls_name)
    proxy.parent = builtins
    return proxy


def _function_type(function, builtins):
    if isinstance(function, scoped_nodes.Lambda):
        if function.root().name == BUILTINS:
            cls_name = "builtin_function_or_method"
        else:
            cls_name = "function"
    elif isinstance(function, bases.BoundMethod):
        cls_name = "method"
    elif isinstance(function, bases.UnboundMethod):
        cls_name = "function"
    return _build_proxy_class(cls_name, builtins)


def _object_type(node, context=None):
    astroid_manager = manager.AstroidManager()
    builtins = astroid_manager.builtins_module
    context = context or contextmod.InferenceContext()

    for inferred in node.infer(context=context):
        if isinstance(inferred, scoped_nodes.ClassDef):
            if inferred.newstyle:
                metaclass = inferred.metaclass(context=context)
                if metaclass:
                    yield metaclass
                    continue
            yield builtins.getattr("type")[0]
        elif isinstance(inferred, (scoped_nodes.Lambda, bases.UnboundMethod)):
            yield _function_type(inferred, builtins)
        elif isinstance(inferred, scoped_nodes.Module):
            yield _build_proxy_class("module", builtins)
        else:
            yield inferred._proxied


def object_type(node, context=None):
    """Obtain the type of the given node

    This is used to implement the ``type`` builtin, which means that it's
    used for inferring type calls, as well as used in a couple of other places
    in the inference.
    The node will be inferred first, so this function can support all
    sorts of objects, as long as they support inference.
    """

    try:
        types = set(_object_type(node, context))
    except exceptions.InferenceError:
        return util.Uninferable
    if len(types) > 1 or not types:
        return util.Uninferable
    return list(types)[0]


def _object_type_is_subclass(obj_type, class_or_seq, context=None):
    if not isinstance(class_or_seq, (tuple, list)):
        class_seq = (class_or_seq,)
    else:
        class_seq = class_or_seq

    if obj_type is util.Uninferable:
        return util.Uninferable

    # Instances are not types
    class_seq = [
        item if not isinstance(item, bases.Instance) else util.Uninferable
        for item in class_seq
    ]
    # strict compatibility with issubclass
    # issubclass(type, (object, 1)) evaluates to true
    # issubclass(object, (1, type)) raises TypeError
    for klass in class_seq:
        if klass is util.Uninferable:
            raise exceptions.AstroidTypeError("arg 2 must be a type or tuple of types")

        for obj_subclass in obj_type.mro():
            if obj_subclass == klass:
                return True
    return False


def object_isinstance(node, class_or_seq, context=None):
    """Check if a node 'isinstance' any node in class_or_seq

    :param node: A given node
    :param class_or_seq: Union[nodes.NodeNG, Sequence[nodes.NodeNG]]
    :rtype: bool

    :raises AstroidTypeError: if the given ``classes_or_seq`` are not types
    """
    obj_type = object_type(node, context)
    if obj_type is util.Uninferable:
        return util.Uninferable
    return _object_type_is_subclass(obj_type, class_or_seq, context=context)


def object_issubclass(node, class_or_seq, context=None):
    """Check if a type is a subclass of any node in class_or_seq

    :param node: A given node
    :param class_or_seq: Union[Nodes.NodeNG, Sequence[nodes.NodeNG]]
    :rtype: bool

    :raises AstroidTypeError: if the given ``classes_or_seq`` are not types
    :raises AstroidError: if the type of the given node cannot be inferred
        or its type's mro doesn't work
    """
    if not isinstance(node, nodes.ClassDef):
        raise TypeError("{node} needs to be a ClassDef node".format(node=node))
    return _object_type_is_subclass(node, class_or_seq, context=context)


def safe_infer(node, context=None):
    """Return the inferred value for the given node.

    Return None if inference failed or if there is some ambiguity (more than
    one node has been inferred).
    """
    try:
        inferit = node.infer(context=context)
        value = next(inferit)
    except exceptions.InferenceError:
        return None
    try:
        next(inferit)
        return None  # None if there is ambiguity on the inferred node
    except exceptions.InferenceError:
        return None  # there is some kind of ambiguity
    except StopIteration:
        return value


def has_known_bases(klass, context=None):
    """Return true if all base classes of a class could be inferred."""
    try:
        return klass._all_bases_known
    except AttributeError:
        pass
    for base in klass.bases:
        result = safe_infer(base, context=context)
        # TODO: check for A->B->A->B pattern in class structure too?
        if (
            not isinstance(result, scoped_nodes.ClassDef)
            or result is klass
            or not has_known_bases(result, context=context)
        ):
            klass._all_bases_known = False
            return False
    klass._all_bases_known = True
    return True


def _type_check(type1, type2):
    if not all(map(has_known_bases, (type1, type2))):
        raise exceptions._NonDeducibleTypeHierarchy

    if not all([type1.newstyle, type2.newstyle]):
        return False
    try:
        return type1 in type2.mro()[:-1]
    except exceptions.MroError:
        # The MRO is invalid.
        raise exceptions._NonDeducibleTypeHierarchy


def is_subtype(type1, type2):
    """Check if *type1* is a subtype of *type2*."""
    return _type_check(type1=type2, type2=type1)


def is_supertype(type1, type2):
    """Check if *type2* is a supertype of *type1*."""
    return _type_check(type1, type2)


def class_instance_as_index(node):
    """Get the value as an index for the given instance.

    If an instance provides an __index__ method, then it can
    be used in some scenarios where an integer is expected,
    for instance when multiplying or subscripting a list.
    """
    context = contextmod.InferenceContext()
    context.callcontext = contextmod.CallContext(args=[node])

    try:
        for inferred in node.igetattr("__index__", context=context):
            if not isinstance(inferred, bases.BoundMethod):
                continue

            for result in inferred.infer_call_result(node, context=context):
                if isinstance(result, nodes.Const) and isinstance(result.value, int):
                    return result
    except exceptions.InferenceError:
        pass
    return None


def object_len(node, context=None):
    """Infer length of given node object

    :param Union[nodes.ClassDef, nodes.Instance] node:
    :param node: Node to infer length of

    :raises AstroidTypeError: If an invalid node is returned
        from __len__ method or no __len__ method exists
    :raises InferenceError: If the given node cannot be inferred
        or if multiple nodes are inferred
    :rtype int: Integer length of node
    """
    # pylint: disable=import-outside-toplevel; circular import
    from astroid.objects import FrozenSet

    inferred_node = safe_infer(node, context=context)
    if inferred_node is None or inferred_node is util.Uninferable:
        raise exceptions.InferenceError(node=node)
    if isinstance(inferred_node, nodes.Const) and isinstance(
        inferred_node.value, (bytes, str)
    ):
        return len(inferred_node.value)
    if isinstance(inferred_node, (nodes.List, nodes.Set, nodes.Tuple, FrozenSet)):
        return len(inferred_node.elts)
    if isinstance(inferred_node, nodes.Dict):
        return len(inferred_node.items)
    try:
        node_type = object_type(inferred_node, context=context)
        len_call = next(node_type.igetattr("__len__", context=context))
    except exceptions.AttributeInferenceError:
        raise exceptions.AstroidTypeError(
            "object of type '{}' has no len()".format(len_call.pytype())
        )

    result_of_len = next(len_call.infer_call_result(node, context))
    if (
        isinstance(result_of_len, nodes.Const)
        and result_of_len.pytype() == "builtins.int"
    ):
        return result_of_len.value
    raise exceptions.AstroidTypeError(
        "'{}' object cannot be interpreted as an integer".format(result_of_len)
    )
