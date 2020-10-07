# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014-2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2015 Rene Zhang <rz99@cornell.edu>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Astroid hooks for various builtins."""

from functools import partial
from textwrap import dedent

import six
from astroid import (
    MANAGER,
    UseInferenceDefault,
    AttributeInferenceError,
    inference_tip,
    InferenceError,
    NameInferenceError,
    AstroidTypeError,
    MroError,
)
from astroid import arguments
from astroid.builder import AstroidBuilder
from astroid import helpers
from astroid import nodes
from astroid import objects
from astroid import scoped_nodes
from astroid import util


OBJECT_DUNDER_NEW = "object.__new__"


def _extend_str(class_node, rvalue):
    """function to extend builtin str/unicode class"""
    code = dedent(
        """
    class whatever(object):
        def join(self, iterable):
            return {rvalue}
        def replace(self, old, new, count=None):
            return {rvalue}
        def format(self, *args, **kwargs):
            return {rvalue}
        def encode(self, encoding='ascii', errors=None):
            return ''
        def decode(self, encoding='ascii', errors=None):
            return u''
        def capitalize(self):
            return {rvalue}
        def title(self):
            return {rvalue}
        def lower(self):
            return {rvalue}
        def upper(self):
            return {rvalue}
        def swapcase(self):
            return {rvalue}
        def index(self, sub, start=None, end=None):
            return 0
        def find(self, sub, start=None, end=None):
            return 0
        def count(self, sub, start=None, end=None):
            return 0
        def strip(self, chars=None):
            return {rvalue}
        def lstrip(self, chars=None):
            return {rvalue}
        def rstrip(self, chars=None):
            return {rvalue}
        def rjust(self, width, fillchar=None):
            return {rvalue}
        def center(self, width, fillchar=None):
            return {rvalue}
        def ljust(self, width, fillchar=None):
            return {rvalue}
    """
    )
    code = code.format(rvalue=rvalue)
    fake = AstroidBuilder(MANAGER).string_build(code)["whatever"]
    for method in fake.mymethods():
        method.parent = class_node
        method.lineno = None
        method.col_offset = None
        if "__class__" in method.locals:
            method.locals["__class__"] = [class_node]
        class_node.locals[method.name] = [method]
        method.parent = class_node


def _extend_builtins(class_transforms):
    builtin_ast = MANAGER.builtins_module
    for class_name, transform in class_transforms.items():
        transform(builtin_ast[class_name])


_extend_builtins(
    {
        "bytes": partial(_extend_str, rvalue="b''"),
        "str": partial(_extend_str, rvalue="''"),
    }
)


def _builtin_filter_predicate(node, builtin_name):
    if isinstance(node.func, nodes.Name) and node.func.name == builtin_name:
        return True
    if isinstance(node.func, nodes.Attribute):
        return (
            node.func.attrname == "fromkeys"
            and isinstance(node.func.expr, nodes.Name)
            and node.func.expr.name == "dict"
        )
    return False


def register_builtin_transform(transform, builtin_name):
    """Register a new transform function for the given *builtin_name*.

    The transform function must accept two parameters, a node and
    an optional context.
    """

    def _transform_wrapper(node, context=None):
        result = transform(node, context=context)
        if result:
            if not result.parent:
                # Let the transformation function determine
                # the parent for its result. Otherwise,
                # we set it to be the node we transformed from.
                result.parent = node

            if result.lineno is None:
                result.lineno = node.lineno
            if result.col_offset is None:
                result.col_offset = node.col_offset
        return iter([result])

    MANAGER.register_transform(
        nodes.Call,
        inference_tip(_transform_wrapper),
        partial(_builtin_filter_predicate, builtin_name=builtin_name),
    )


def _container_generic_inference(node, context, node_type, transform):
    args = node.args
    if not args:
        return node_type()
    if len(node.args) > 1:
        raise UseInferenceDefault()

    arg, = args
    transformed = transform(arg)
    if not transformed:
        try:
            inferred = next(arg.infer(context=context))
        except (InferenceError, StopIteration):
            raise UseInferenceDefault()
        if inferred is util.Uninferable:
            raise UseInferenceDefault()
        transformed = transform(inferred)
    if not transformed or transformed is util.Uninferable:
        raise UseInferenceDefault()
    return transformed


def _container_generic_transform(arg, klass, iterables, build_elts):
    if isinstance(arg, klass):
        return arg
    elif isinstance(arg, iterables):
        if all(isinstance(elt, nodes.Const) for elt in arg.elts):
            elts = [elt.value for elt in arg.elts]
        else:
            # TODO: Does not handle deduplication for sets.
            elts = filter(None, map(helpers.safe_infer, arg.elts))
    elif isinstance(arg, nodes.Dict):
        # Dicts need to have consts as strings already.
        if not all(isinstance(elt[0], nodes.Const) for elt in arg.items):
            raise UseInferenceDefault()
        elts = [item[0].value for item in arg.items]
    elif isinstance(arg, nodes.Const) and isinstance(
        arg.value, (six.string_types, six.binary_type)
    ):
        elts = arg.value
    else:
        return
    return klass.from_elements(elts=build_elts(elts))


def _infer_builtin_container(
    node, context, klass=None, iterables=None, build_elts=None
):
    transform_func = partial(
        _container_generic_transform,
        klass=klass,
        iterables=iterables,
        build_elts=build_elts,
    )

    return _container_generic_inference(node, context, klass, transform_func)


# pylint: disable=invalid-name
infer_tuple = partial(
    _infer_builtin_container,
    klass=nodes.Tuple,
    iterables=(
        nodes.List,
        nodes.Set,
        objects.FrozenSet,
        objects.DictItems,
        objects.DictKeys,
        objects.DictValues,
    ),
    build_elts=tuple,
)

infer_list = partial(
    _infer_builtin_container,
    klass=nodes.List,
    iterables=(
        nodes.Tuple,
        nodes.Set,
        objects.FrozenSet,
        objects.DictItems,
        objects.DictKeys,
        objects.DictValues,
    ),
    build_elts=list,
)

infer_set = partial(
    _infer_builtin_container,
    klass=nodes.Set,
    iterables=(nodes.List, nodes.Tuple, objects.FrozenSet, objects.DictKeys),
    build_elts=set,
)

infer_frozenset = partial(
    _infer_builtin_container,
    klass=objects.FrozenSet,
    iterables=(nodes.List, nodes.Tuple, nodes.Set, objects.FrozenSet, objects.DictKeys),
    build_elts=frozenset,
)


def _get_elts(arg, context):
    is_iterable = lambda n: isinstance(n, (nodes.List, nodes.Tuple, nodes.Set))
    try:
        inferred = next(arg.infer(context))
    except (InferenceError, NameInferenceError):
        raise UseInferenceDefault()
    if isinstance(inferred, nodes.Dict):
        items = inferred.items
    elif is_iterable(inferred):
        items = []
        for elt in inferred.elts:
            # If an item is not a pair of two items,
            # then fallback to the default inference.
            # Also, take in consideration only hashable items,
            # tuples and consts. We are choosing Names as well.
            if not is_iterable(elt):
                raise UseInferenceDefault()
            if len(elt.elts) != 2:
                raise UseInferenceDefault()
            if not isinstance(elt.elts[0], (nodes.Tuple, nodes.Const, nodes.Name)):
                raise UseInferenceDefault()
            items.append(tuple(elt.elts))
    else:
        raise UseInferenceDefault()
    return items


def infer_dict(node, context=None):
    """Try to infer a dict call to a Dict node.

    The function treats the following cases:

        * dict()
        * dict(mapping)
        * dict(iterable)
        * dict(iterable, **kwargs)
        * dict(mapping, **kwargs)
        * dict(**kwargs)

    If a case can't be inferred, we'll fallback to default inference.
    """
    call = arguments.CallSite.from_call(node)
    if call.has_invalid_arguments() or call.has_invalid_keywords():
        raise UseInferenceDefault

    args = call.positional_arguments
    kwargs = list(call.keyword_arguments.items())

    if not args and not kwargs:
        # dict()
        return nodes.Dict()
    elif kwargs and not args:
        # dict(a=1, b=2, c=4)
        items = [(nodes.Const(key), value) for key, value in kwargs]
    elif len(args) == 1 and kwargs:
        # dict(some_iterable, b=2, c=4)
        elts = _get_elts(args[0], context)
        keys = [(nodes.Const(key), value) for key, value in kwargs]
        items = elts + keys
    elif len(args) == 1:
        items = _get_elts(args[0], context)
    else:
        raise UseInferenceDefault()

    value = nodes.Dict(
        col_offset=node.col_offset, lineno=node.lineno, parent=node.parent
    )
    value.postinit(items)
    return value


def infer_super(node, context=None):
    """Understand super calls.

    There are some restrictions for what can be understood:

        * unbounded super (one argument form) is not understood.

        * if the super call is not inside a function (classmethod or method),
          then the default inference will be used.

        * if the super arguments can't be inferred, the default inference
          will be used.
    """
    if len(node.args) == 1:
        # Ignore unbounded super.
        raise UseInferenceDefault

    scope = node.scope()
    if not isinstance(scope, nodes.FunctionDef):
        # Ignore non-method uses of super.
        raise UseInferenceDefault
    if scope.type not in ("classmethod", "method"):
        # Not interested in staticmethods.
        raise UseInferenceDefault

    cls = scoped_nodes.get_wrapping_class(scope)
    if not len(node.args):
        mro_pointer = cls
        # In we are in a classmethod, the interpreter will fill
        # automatically the class as the second argument, not an instance.
        if scope.type == "classmethod":
            mro_type = cls
        else:
            mro_type = cls.instantiate_class()
    else:
        try:
            mro_pointer = next(node.args[0].infer(context=context))
        except InferenceError:
            raise UseInferenceDefault
        try:
            mro_type = next(node.args[1].infer(context=context))
        except InferenceError:
            raise UseInferenceDefault

    if mro_pointer is util.Uninferable or mro_type is util.Uninferable:
        # No way we could understand this.
        raise UseInferenceDefault

    super_obj = objects.Super(
        mro_pointer=mro_pointer, mro_type=mro_type, self_class=cls, scope=scope
    )
    super_obj.parent = node
    return super_obj


def _infer_getattr_args(node, context):
    if len(node.args) not in (2, 3):
        # Not a valid getattr call.
        raise UseInferenceDefault

    try:
        obj = next(node.args[0].infer(context=context))
        attr = next(node.args[1].infer(context=context))
    except InferenceError:
        raise UseInferenceDefault

    if obj is util.Uninferable or attr is util.Uninferable:
        # If one of the arguments is something we can't infer,
        # then also make the result of the getattr call something
        # which is unknown.
        return util.Uninferable, util.Uninferable

    is_string = isinstance(attr, nodes.Const) and isinstance(
        attr.value, six.string_types
    )
    if not is_string:
        raise UseInferenceDefault

    return obj, attr.value


def infer_getattr(node, context=None):
    """Understand getattr calls

    If one of the arguments is an Uninferable object, then the
    result will be an Uninferable object. Otherwise, the normal attribute
    lookup will be done.
    """
    obj, attr = _infer_getattr_args(node, context)
    if (
        obj is util.Uninferable
        or attr is util.Uninferable
        or not hasattr(obj, "igetattr")
    ):
        return util.Uninferable

    try:
        return next(obj.igetattr(attr, context=context))
    except (StopIteration, InferenceError, AttributeInferenceError):
        if len(node.args) == 3:
            # Try to infer the default and return it instead.
            try:
                return next(node.args[2].infer(context=context))
            except InferenceError:
                raise UseInferenceDefault

    raise UseInferenceDefault


def infer_hasattr(node, context=None):
    """Understand hasattr calls

    This always guarantees three possible outcomes for calling
    hasattr: Const(False) when we are sure that the object
    doesn't have the intended attribute, Const(True) when
    we know that the object has the attribute and Uninferable
    when we are unsure of the outcome of the function call.
    """
    try:
        obj, attr = _infer_getattr_args(node, context)
        if (
            obj is util.Uninferable
            or attr is util.Uninferable
            or not hasattr(obj, "getattr")
        ):
            return util.Uninferable
        obj.getattr(attr, context=context)
    except UseInferenceDefault:
        # Can't infer something from this function call.
        return util.Uninferable
    except AttributeInferenceError:
        # Doesn't have it.
        return nodes.Const(False)
    return nodes.Const(True)


def infer_callable(node, context=None):
    """Understand callable calls

    This follows Python's semantics, where an object
    is callable if it provides an attribute __call__,
    even though that attribute is something which can't be
    called.
    """
    if len(node.args) != 1:
        # Invalid callable call.
        raise UseInferenceDefault

    argument = node.args[0]
    try:
        inferred = next(argument.infer(context=context))
    except InferenceError:
        return util.Uninferable
    if inferred is util.Uninferable:
        return util.Uninferable
    return nodes.Const(inferred.callable())


def infer_bool(node, context=None):
    """Understand bool calls."""
    if len(node.args) > 1:
        # Invalid bool call.
        raise UseInferenceDefault

    if not node.args:
        return nodes.Const(False)

    argument = node.args[0]
    try:
        inferred = next(argument.infer(context=context))
    except InferenceError:
        return util.Uninferable
    if inferred is util.Uninferable:
        return util.Uninferable

    bool_value = inferred.bool_value()
    if bool_value is util.Uninferable:
        return util.Uninferable
    return nodes.Const(bool_value)


def infer_type(node, context=None):
    """Understand the one-argument form of *type*."""
    if len(node.args) != 1:
        raise UseInferenceDefault

    return helpers.object_type(node.args[0], context)


def infer_slice(node, context=None):
    """Understand `slice` calls."""
    args = node.args
    if not 0 < len(args) <= 3:
        raise UseInferenceDefault

    infer_func = partial(helpers.safe_infer, context=context)
    args = [infer_func(arg) for arg in args]
    for arg in args:
        if not arg or arg is util.Uninferable:
            raise UseInferenceDefault
        if not isinstance(arg, nodes.Const):
            raise UseInferenceDefault
        if not isinstance(arg.value, (type(None), int)):
            raise UseInferenceDefault

    if len(args) < 3:
        # Make sure we have 3 arguments.
        args.extend([None] * (3 - len(args)))

    slice_node = nodes.Slice(
        lineno=node.lineno, col_offset=node.col_offset, parent=node.parent
    )
    slice_node.postinit(*args)
    return slice_node


def _infer_object__new__decorator(node, context=None):
    # Instantiate class immediately
    # since that's what @object.__new__ does
    return iter((node.instantiate_class(),))


def _infer_object__new__decorator_check(node):
    """Predicate before inference_tip

    Check if the given ClassDef has an @object.__new__ decorator
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if isinstance(decorator, nodes.Attribute):
            if decorator.as_string() == OBJECT_DUNDER_NEW:
                return True
    return False


def infer_issubclass(callnode, context=None):
    """Infer issubclass() calls

    :param nodes.Call callnode: an `issubclass` call
    :param InferenceContext: the context for the inference
    :rtype nodes.Const: Boolean Const value of the `issubclass` call
    :raises UseInferenceDefault: If the node cannot be inferred
    """
    call = arguments.CallSite.from_call(callnode)
    if call.keyword_arguments:
        # issubclass doesn't support keyword arguments
        raise UseInferenceDefault("TypeError: issubclass() takes no keyword arguments")
    if len(call.positional_arguments) != 2:
        raise UseInferenceDefault(
            "Expected two arguments, got {count}".format(
                count=len(call.positional_arguments)
            )
        )
    # The left hand argument is the obj to be checked
    obj_node, class_or_tuple_node = call.positional_arguments

    try:
        obj_type = next(obj_node.infer(context=context))
    except InferenceError as exc:
        raise UseInferenceDefault from exc
    if not isinstance(obj_type, nodes.ClassDef):
        raise UseInferenceDefault("TypeError: arg 1 must be class")

    # The right hand argument is the class(es) that the given
    # object is to be checked against.
    try:
        class_container = _class_or_tuple_to_container(
            class_or_tuple_node, context=context
        )
    except InferenceError as exc:
        raise UseInferenceDefault from exc
    try:
        issubclass_bool = helpers.object_issubclass(obj_type, class_container, context)
    except AstroidTypeError as exc:
        raise UseInferenceDefault("TypeError: " + str(exc)) from exc
    except MroError as exc:
        raise UseInferenceDefault from exc
    return nodes.Const(issubclass_bool)


def infer_isinstance(callnode, context=None):
    """Infer isinstance calls

    :param nodes.Call callnode: an isinstance call
    :param InferenceContext: context for call
        (currently unused but is a common interface for inference)
    :rtype nodes.Const: Boolean Const value of isinstance call

    :raises UseInferenceDefault: If the node cannot be inferred
    """
    call = arguments.CallSite.from_call(callnode)
    if call.keyword_arguments:
        # isinstance doesn't support keyword arguments
        raise UseInferenceDefault("TypeError: isinstance() takes no keyword arguments")
    if len(call.positional_arguments) != 2:
        raise UseInferenceDefault(
            "Expected two arguments, got {count}".format(
                count=len(call.positional_arguments)
            )
        )
    # The left hand argument is the obj to be checked
    obj_node, class_or_tuple_node = call.positional_arguments
    # The right hand argument is the class(es) that the given
    # obj is to be check is an instance of
    try:
        class_container = _class_or_tuple_to_container(
            class_or_tuple_node, context=context
        )
    except InferenceError:
        raise UseInferenceDefault
    try:
        isinstance_bool = helpers.object_isinstance(obj_node, class_container, context)
    except AstroidTypeError as exc:
        raise UseInferenceDefault("TypeError: " + str(exc))
    except MroError as exc:
        raise UseInferenceDefault from exc
    if isinstance_bool is util.Uninferable:
        raise UseInferenceDefault
    return nodes.Const(isinstance_bool)


def _class_or_tuple_to_container(node, context=None):
    # Move inferences results into container
    # to simplify later logic
    # raises InferenceError if any of the inferences fall through
    node_infer = next(node.infer(context=context))
    # arg2 MUST be a type or a TUPLE of types
    # for isinstance
    if isinstance(node_infer, nodes.Tuple):
        class_container = [
            next(node.infer(context=context)) for node in node_infer.elts
        ]
        class_container = [
            klass_node for klass_node in class_container if klass_node is not None
        ]
    else:
        class_container = [node_infer]
    return class_container


def infer_len(node, context=None):
    """Infer length calls

    :param nodes.Call node: len call to infer
    :param context.InferenceContext: node context
    :rtype nodes.Const: a Const node with the inferred length, if possible
    """
    call = arguments.CallSite.from_call(node)
    if call.keyword_arguments:
        raise UseInferenceDefault("TypeError: len() must take no keyword arguments")
    if len(call.positional_arguments) != 1:
        raise UseInferenceDefault(
            "TypeError: len() must take exactly one argument "
            "({len}) given".format(len=len(call.positional_arguments))
        )
    [argument_node] = call.positional_arguments
    try:
        return nodes.Const(helpers.object_len(argument_node, context=context))
    except (AstroidTypeError, InferenceError) as exc:
        raise UseInferenceDefault(str(exc)) from exc


def infer_str(node, context=None):
    """Infer str() calls

    :param nodes.Call node: str() call to infer
    :param context.InferenceContext: node context
    :rtype nodes.Const: a Const containing an empty string
    """
    call = arguments.CallSite.from_call(node)
    if call.keyword_arguments:
        raise UseInferenceDefault("TypeError: str() must take no keyword arguments")
    try:
        return nodes.Const("")
    except (AstroidTypeError, InferenceError) as exc:
        raise UseInferenceDefault(str(exc)) from exc


def infer_int(node, context=None):
    """Infer int() calls

    :param nodes.Call node: int() call to infer
    :param context.InferenceContext: node context
    :rtype nodes.Const: a Const containing the integer value of the int() call
    """
    call = arguments.CallSite.from_call(node)
    if call.keyword_arguments:
        raise UseInferenceDefault("TypeError: int() must take no keyword arguments")

    if call.positional_arguments:
        try:
            first_value = next(call.positional_arguments[0].infer(context=context))
        except InferenceError as exc:
            raise UseInferenceDefault(str(exc)) from exc

        if first_value is util.Uninferable:
            raise UseInferenceDefault

        if isinstance(first_value, nodes.Const) and isinstance(
            first_value.value, (int, str)
        ):
            try:
                actual_value = int(first_value.value)
            except ValueError:
                return nodes.Const(0)
            return nodes.Const(actual_value)

    return nodes.Const(0)


def infer_dict_fromkeys(node, context=None):
    """Infer dict.fromkeys

    :param nodes.Call node: dict.fromkeys() call to infer
    :param context.InferenceContext: node context
    :rtype nodes.Dict:
        a Dictionary containing the values that astroid was able to infer.
        In case the inference failed for any reason, an empty dictionary
        will be inferred instead.
    """

    def _build_dict_with_elements(elements):
        new_node = nodes.Dict(
            col_offset=node.col_offset, lineno=node.lineno, parent=node.parent
        )
        new_node.postinit(elements)
        return new_node

    call = arguments.CallSite.from_call(node)
    if call.keyword_arguments:
        raise UseInferenceDefault("TypeError: int() must take no keyword arguments")
    if len(call.positional_arguments) not in {1, 2}:
        raise UseInferenceDefault(
            "TypeError: Needs between 1 and 2 positional arguments"
        )

    default = nodes.Const(None)
    values = call.positional_arguments[0]
    try:
        inferred_values = next(values.infer(context=context))
    except InferenceError:
        return _build_dict_with_elements([])
    if inferred_values is util.Uninferable:
        return _build_dict_with_elements([])

    # Limit to a couple of potential values, as this can become pretty complicated
    accepted_iterable_elements = (nodes.Const,)
    if isinstance(inferred_values, (nodes.List, nodes.Set, nodes.Tuple)):
        elements = inferred_values.elts
        for element in elements:
            if not isinstance(element, accepted_iterable_elements):
                # Fallback to an empty dict
                return _build_dict_with_elements([])

        elements_with_value = [(element, default) for element in elements]
        return _build_dict_with_elements(elements_with_value)

    elif isinstance(inferred_values, nodes.Const) and isinstance(
        inferred_values.value, (str, bytes)
    ):
        elements = [
            (nodes.Const(element), default) for element in inferred_values.value
        ]
        return _build_dict_with_elements(elements)
    elif isinstance(inferred_values, nodes.Dict):
        keys = inferred_values.itered()
        for key in keys:
            if not isinstance(key, accepted_iterable_elements):
                # Fallback to an empty dict
                return _build_dict_with_elements([])

        elements_with_value = [(element, default) for element in keys]
        return _build_dict_with_elements(elements_with_value)

    # Fallback to an empty dictionary
    return _build_dict_with_elements([])


# Builtins inference
register_builtin_transform(infer_bool, "bool")
register_builtin_transform(infer_super, "super")
register_builtin_transform(infer_callable, "callable")
register_builtin_transform(infer_getattr, "getattr")
register_builtin_transform(infer_hasattr, "hasattr")
register_builtin_transform(infer_tuple, "tuple")
register_builtin_transform(infer_set, "set")
register_builtin_transform(infer_list, "list")
register_builtin_transform(infer_dict, "dict")
register_builtin_transform(infer_frozenset, "frozenset")
register_builtin_transform(infer_type, "type")
register_builtin_transform(infer_slice, "slice")
register_builtin_transform(infer_isinstance, "isinstance")
register_builtin_transform(infer_issubclass, "issubclass")
register_builtin_transform(infer_len, "len")
register_builtin_transform(infer_str, "str")
register_builtin_transform(infer_int, "int")
register_builtin_transform(infer_dict_fromkeys, "dict.fromkeys")


# Infer object.__new__ calls
MANAGER.register_transform(
    nodes.ClassDef,
    inference_tip(_infer_object__new__decorator),
    _infer_object__new__decorator_check,
)
