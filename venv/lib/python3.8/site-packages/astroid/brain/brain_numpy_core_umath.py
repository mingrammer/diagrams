# Copyright (c) 2018-2019 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for numpy.core.umath module."""

import astroid


def numpy_core_umath_transform():
    ufunc_optional_keyword_arguments = (
        """out=None, where=True, casting='same_kind', order='K', """
        """dtype=None, subok=True"""
    )
    return astroid.parse(
        """
    # Constants
    e = 2.718281828459045
    euler_gamma = 0.5772156649015329

    # No arg functions
    def geterrobj(): return []

    # One arg functions
    def seterrobj(errobj): return None

    # One arg functions with optional kwargs
    def arccos(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def arccosh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def arcsin(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def arcsinh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def arctan(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def arctanh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def cbrt(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def conj(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def conjugate(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def cosh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def deg2rad(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def degrees(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def exp2(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def expm1(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def fabs(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def frexp(x, {opt_args:s}): return (numpy.ndarray((0, 0)), numpy.ndarray((0, 0)))
    def isfinite(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def isinf(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def log(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def log1p(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def log2(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def logical_not(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def modf(x, {opt_args:s}): return (numpy.ndarray((0, 0)), numpy.ndarray((0, 0)))
    def negative(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def rad2deg(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def radians(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def reciprocal(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def rint(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def sign(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def signbit(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def sinh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def spacing(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def square(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def tan(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def tanh(x, {opt_args:s}): return numpy.ndarray((0, 0))
    def trunc(x, {opt_args:s}): return numpy.ndarray((0, 0))

    # Two args functions with optional kwargs
    def bitwise_and(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def bitwise_or(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def bitwise_xor(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def copysign(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def divide(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def equal(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def floor_divide(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def fmax(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def fmin(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def fmod(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def greater(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def hypot(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def ldexp(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def left_shift(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def less(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def logaddexp(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def logaddexp2(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def logical_and(x1, x2, {opt_args:s}): return numpy.ndarray([0, 0])
    def logical_or(x1, x2, {opt_args:s}): return numpy.ndarray([0, 0])
    def logical_xor(x1, x2, {opt_args:s}): return numpy.ndarray([0, 0])
    def maximum(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def minimum(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def nextafter(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def not_equal(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def power(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def remainder(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def right_shift(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def subtract(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    def true_divide(x1, x2, {opt_args:s}): return numpy.ndarray((0, 0))
    """.format(
            opt_args=ufunc_optional_keyword_arguments
        )
    )


astroid.register_module_extender(
    astroid.MANAGER, "numpy.core.umath", numpy_core_umath_transform
)
