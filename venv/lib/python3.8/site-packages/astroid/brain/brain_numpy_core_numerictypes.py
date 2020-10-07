# Copyright (c) 2018-2019 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

# TODO(hippo91) : correct the methods signature.

"""Astroid hooks for numpy.core.numerictypes module."""

import astroid


def numpy_core_numerictypes_transform():
    return astroid.parse(
        """
    # different types defined in numerictypes.py
    class generic(object):
        def __init__(self, value):
            self.T = None
            self.base = None
            self.data = None
            self.dtype = None
            self.flags = None
            self.flat = None
            self.imag = None
            self.itemsize = None
            self.nbytes = None
            self.ndim = None
            self.real = None
            self.size = None
            self.strides = None

        def all(self): return uninferable
        def any(self): return uninferable
        def argmax(self): return uninferable
        def argmin(self): return uninferable
        def argsort(self): return uninferable
        def astype(self): return uninferable
        def base(self): return uninferable
        def byteswap(self): return uninferable
        def choose(self): return uninferable
        def clip(self): return uninferable
        def compress(self): return uninferable
        def conj(self): return uninferable
        def conjugate(self): return uninferable
        def copy(self): return uninferable
        def cumprod(self): return uninferable
        def cumsum(self): return uninferable
        def data(self): return uninferable
        def diagonal(self): return uninferable
        def dtype(self): return uninferable
        def dump(self): return uninferable
        def dumps(self): return uninferable
        def fill(self): return uninferable
        def flags(self): return uninferable
        def flat(self): return uninferable
        def flatten(self): return uninferable
        def getfield(self): return uninferable
        def imag(self): return uninferable
        def item(self): return uninferable
        def itemset(self): return uninferable
        def itemsize(self): return uninferable
        def max(self): return uninferable
        def mean(self): return uninferable
        def min(self): return uninferable
        def nbytes(self): return uninferable
        def ndim(self): return uninferable
        def newbyteorder(self): return uninferable
        def nonzero(self): return uninferable
        def prod(self): return uninferable
        def ptp(self): return uninferable
        def put(self): return uninferable
        def ravel(self): return uninferable
        def real(self): return uninferable
        def repeat(self): return uninferable
        def reshape(self): return uninferable
        def resize(self): return uninferable
        def round(self): return uninferable
        def searchsorted(self): return uninferable
        def setfield(self): return uninferable
        def setflags(self): return uninferable
        def shape(self): return uninferable
        def size(self): return uninferable
        def sort(self): return uninferable
        def squeeze(self): return uninferable
        def std(self): return uninferable
        def strides(self): return uninferable
        def sum(self): return uninferable
        def swapaxes(self): return uninferable
        def take(self): return uninferable
        def tobytes(self): return uninferable
        def tofile(self): return uninferable
        def tolist(self): return uninferable
        def tostring(self): return uninferable
        def trace(self): return uninferable
        def transpose(self): return uninferable
        def var(self): return uninferable
        def view(self): return uninferable


    class dtype(object):
        def __init__(self, obj, align=False, copy=False):
            self.alignment = None
            self.base = None
            self.byteorder = None
            self.char = None
            self.descr = None
            self.fields = None
            self.flags = None
            self.hasobject = None
            self.isalignedstruct = None
            self.isbuiltin = None
            self.isnative = None
            self.itemsize = None
            self.kind = None
            self.metadata = None
            self.name = None
            self.names = None
            self.num = None
            self.shape = None
            self.str = None
            self.subdtype = None
            self.type = None

        def newbyteorder(self, new_order='S'): return uninferable
        def __neg__(self): return uninferable

    class busdaycalendar(object):
        def __init__(self, weekmask='1111100', holidays=None):
            self.holidays = None
            self.weekmask = None

    class flexible(generic): pass
    class bool_(generic): pass
    class number(generic):
        def __neg__(self): return uninferable
    class datetime64(generic):
        def __init__(self, nb, unit=None): pass


    class void(flexible):
        def __init__(self, *args, **kwargs):
            self.base = None
            self.dtype = None
            self.flags = None
        def getfield(self): return uninferable
        def setfield(self): return uninferable


    class character(flexible): pass


    class integer(number):
        def __init__(self, value):
           self.denominator = None
           self.numerator = None


    class inexact(number): pass


    class str_(str, character):
        def maketrans(self, x, y=None, z=None): return uninferable


    class bytes_(bytes, character):
        def fromhex(self, string): return uninferable
        def maketrans(self, frm, to): return uninferable


    class signedinteger(integer): pass


    class unsignedinteger(integer): pass


    class complexfloating(inexact): pass


    class floating(inexact): pass


    class float64(floating, float):
        def fromhex(self, string): return uninferable


    class uint64(unsignedinteger): pass
    class complex64(complexfloating): pass
    class int16(signedinteger): pass
    class float96(floating): pass
    class int8(signedinteger): pass
    class uint32(unsignedinteger): pass
    class uint8(unsignedinteger): pass
    class _typedict(dict): pass
    class complex192(complexfloating): pass
    class timedelta64(signedinteger):
        def __init__(self, nb, unit=None): pass
    class int32(signedinteger): pass
    class uint16(unsignedinteger): pass
    class float32(floating): pass
    class complex128(complexfloating, complex): pass
    class float16(floating): pass
    class int64(signedinteger): pass

    buffer_type = memoryview
    bool8 = bool_
    byte = int8
    bytes0 = bytes_
    cdouble = complex128
    cfloat = complex128
    clongdouble = complex192
    clongfloat = complex192
    complex_ = complex128
    csingle = complex64
    double = float64
    float_ = float64
    half = float16
    int0 = int32
    int_ = int32
    intc = int32
    intp = int32
    long = int32
    longcomplex = complex192
    longdouble = float96
    longfloat = float96
    longlong = int64
    object0 = object_
    object_ = object_
    short = int16
    single = float32
    singlecomplex = complex64
    str0 = str_
    string_ = bytes_
    ubyte = uint8
    uint = uint32
    uint0 = uint32
    uintc = uint32
    uintp = uint32
    ulonglong = uint64
    unicode = str_
    unicode_ = str_
    ushort = uint16
    void0 = void
    """
    )


astroid.register_module_extender(
    astroid.MANAGER, "numpy.core.numerictypes", numpy_core_numerictypes_transform
)
