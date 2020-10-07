# Copyright (c) 2018-2019 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for numpy.core.multiarray module."""

import functools
import astroid
from brain_numpy_utils import looks_like_numpy_member, infer_numpy_member


def numpy_core_multiarray_transform():
    return astroid.parse(
        """
    # different functions defined in multiarray.py
    def inner(a, b):
        return numpy.ndarray([0, 0])

    def vdot(a, b):
        return numpy.ndarray([0, 0])
        """
    )


astroid.register_module_extender(
    astroid.MANAGER, "numpy.core.multiarray", numpy_core_multiarray_transform
)


METHODS_TO_BE_INFERRED = {
    "array": """def array(object, dtype=None, copy=True, order='K', subok=False, ndmin=0):
            return numpy.ndarray([0, 0])""",
    "dot": """def dot(a, b, out=None):
            return numpy.ndarray([0, 0])""",
    "empty_like": """def empty_like(a, dtype=None, order='K', subok=True):
            return numpy.ndarray((0, 0))""",
    "concatenate": """def concatenate(arrays, axis=None, out=None):
            return numpy.ndarray((0, 0))""",
    "where": """def where(condition, x=None, y=None):
            return numpy.ndarray([0, 0])""",
    "empty": """def empty(shape, dtype=float, order='C'):
            return numpy.ndarray([0, 0])""",
    "zeros": """def zeros(shape, dtype=float, order='C'):
            return numpy.ndarray([0, 0])""",
}

for method_name, function_src in METHODS_TO_BE_INFERRED.items():
    inference_function = functools.partial(infer_numpy_member, function_src)
    astroid.MANAGER.register_transform(
        astroid.Attribute,
        astroid.inference_tip(inference_function),
        functools.partial(looks_like_numpy_member, method_name),
    )
