# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
"""
Astroid hook for the dataclasses library
"""

import astroid
from astroid import MANAGER


DATACLASSES_DECORATORS = frozenset(("dataclasses.dataclass", "dataclass"))


def is_decorated_with_dataclass(node, decorator_names=DATACLASSES_DECORATORS):
    """Return True if a decorated node has a `dataclass` decorator applied."""
    if not node.decorators:
        return False
    for decorator_attribute in node.decorators.nodes:
        if isinstance(decorator_attribute, astroid.Call):  # decorator with arguments
            decorator_attribute = decorator_attribute.func
        if decorator_attribute.as_string() in decorator_names:
            return True
    return False


def dataclass_transform(node):
    """Rewrite a dataclass to be easily understood by pylint"""

    for assign_node in node.body:
        if not isinstance(assign_node, (astroid.AnnAssign, astroid.Assign)):
            continue

        targets = (
            assign_node.targets
            if hasattr(assign_node, "targets")
            else [assign_node.target]
        )
        for target in targets:
            rhs_node = astroid.Unknown(
                lineno=assign_node.lineno,
                col_offset=assign_node.col_offset,
                parent=assign_node,
            )
            node.instance_attrs[target.name] = [rhs_node]
            node.locals[target.name] = [rhs_node]


MANAGER.register_transform(
    astroid.ClassDef, dataclass_transform, is_decorated_with_dataclass
)
