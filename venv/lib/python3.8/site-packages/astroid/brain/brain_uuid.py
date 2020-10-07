# Copyright (c) 2017 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Astroid hooks for the UUID module."""


from astroid import MANAGER
from astroid import nodes


def _patch_uuid_class(node):
    # The .int member is patched using __dict__
    node.locals["int"] = [nodes.Const(0, parent=node)]


MANAGER.register_transform(
    nodes.ClassDef, _patch_uuid_class, lambda node: node.qname() == "uuid.UUID"
)
