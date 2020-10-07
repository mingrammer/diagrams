# Copyright (c) 2018-2019 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for numpy.core.fromnumeric module."""

import astroid


def numpy_core_fromnumeric_transform():
    return astroid.parse(
        """
    def sum(a, axis=None, dtype=None, out=None, keepdims=None, initial=None):
        return numpy.ndarray([0, 0])
    """
    )


astroid.register_module_extender(
    astroid.MANAGER, "numpy.core.fromnumeric", numpy_core_fromnumeric_transform
)
