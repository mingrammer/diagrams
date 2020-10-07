# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import random

import astroid
from astroid import helpers
from astroid import MANAGER


ACCEPTED_ITERABLES_FOR_SAMPLE = (astroid.List, astroid.Set, astroid.Tuple)


def _clone_node_with_lineno(node, parent, lineno):
    cls = node.__class__
    other_fields = node._other_fields
    _astroid_fields = node._astroid_fields
    init_params = {"lineno": lineno, "col_offset": node.col_offset, "parent": parent}
    postinit_params = {param: getattr(node, param) for param in _astroid_fields}
    if other_fields:
        init_params.update({param: getattr(node, param) for param in other_fields})
    new_node = cls(**init_params)
    if hasattr(node, "postinit") and _astroid_fields:
        new_node.postinit(**postinit_params)
    return new_node


def infer_random_sample(node, context=None):
    if len(node.args) != 2:
        raise astroid.UseInferenceDefault

    length = node.args[1]
    if not isinstance(length, astroid.Const):
        raise astroid.UseInferenceDefault
    if not isinstance(length.value, int):
        raise astroid.UseInferenceDefault

    inferred_sequence = helpers.safe_infer(node.args[0], context=context)
    if not inferred_sequence:
        raise astroid.UseInferenceDefault

    if not isinstance(inferred_sequence, ACCEPTED_ITERABLES_FOR_SAMPLE):
        raise astroid.UseInferenceDefault

    if length.value > len(inferred_sequence.elts):
        # In this case, this will raise a ValueError
        raise astroid.UseInferenceDefault

    try:
        elts = random.sample(inferred_sequence.elts, length.value)
    except ValueError:
        raise astroid.UseInferenceDefault

    new_node = astroid.List(
        lineno=node.lineno, col_offset=node.col_offset, parent=node.scope()
    )
    new_elts = [
        _clone_node_with_lineno(elt, parent=new_node, lineno=new_node.lineno)
        for elt in elts
    ]
    new_node.postinit(new_elts)
    return iter((new_node,))


def _looks_like_random_sample(node):
    func = node.func
    if isinstance(func, astroid.Attribute):
        return func.attrname == "sample"
    if isinstance(func, astroid.Name):
        return func.name == "sample"
    return False


MANAGER.register_transform(
    astroid.Call, astroid.inference_tip(infer_random_sample), _looks_like_random_sample
)
