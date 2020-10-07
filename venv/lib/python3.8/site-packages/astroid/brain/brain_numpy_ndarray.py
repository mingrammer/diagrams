# Copyright (c) 2015-2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER


"""Astroid hooks for numpy ndarray class."""

import functools
import astroid


def infer_numpy_ndarray(node, context=None):
    ndarray = """
    class ndarray(object):
        def __init__(self, shape, dtype=float, buffer=None, offset=0,
                     strides=None, order=None):
            self.T = None
            self.base = None
            self.ctypes = None
            self.data = None
            self.dtype = None
            self.flags = None
            self.flat = None
            self.imag = None
            self.itemsize = None
            self.nbytes = None
            self.ndim = None
            self.real = None
            self.shape = None
            self.size = None
            self.strides = None

        def __abs__(self): return numpy.ndarray([0, 0])
        def __add__(self, value): return numpy.ndarray([0, 0]) 
        def __and__(self, value): return numpy.ndarray([0, 0]) 
        def __array__(self, dtype=None): return numpy.ndarray([0, 0]) 
        def __array_wrap__(self, obj): return numpy.ndarray([0, 0]) 
        def __contains__(self, key): return True
        def __copy__(self): return numpy.ndarray([0, 0])
        def __deepcopy__(self, memo): return numpy.ndarray([0, 0])
        def __divmod__(self, value): return (numpy.ndarray([0, 0]), numpy.ndarray([0, 0]))
        def __eq__(self, value): return numpy.ndarray([0, 0])
        def __float__(self): return 0.
        def __floordiv__(self): return numpy.ndarray([0, 0])
        def __ge__(self, value): return numpy.ndarray([0, 0])
        def __getitem__(self, key): return uninferable
        def __gt__(self, value): return numpy.ndarray([0, 0])
        def __iadd__(self, value): return numpy.ndarray([0, 0])
        def __iand__(self, value): return numpy.ndarray([0, 0])
        def __ifloordiv__(self, value): return numpy.ndarray([0, 0])
        def __ilshift__(self, value): return numpy.ndarray([0, 0])
        def __imod__(self, value): return numpy.ndarray([0, 0])
        def __imul__(self, value): return numpy.ndarray([0, 0])
        def __int__(self): return 0
        def __invert__(self): return numpy.ndarray([0, 0])
        def __ior__(self, value): return numpy.ndarray([0, 0])
        def __ipow__(self, value): return numpy.ndarray([0, 0])
        def __irshift__(self, value): return numpy.ndarray([0, 0])
        def __isub__(self, value): return numpy.ndarray([0, 0])
        def __itruediv__(self, value): return numpy.ndarray([0, 0])
        def __ixor__(self, value): return numpy.ndarray([0, 0])
        def __le__(self, value): return numpy.ndarray([0, 0])
        def __len__(self): return 1
        def __lshift__(self, value): return numpy.ndarray([0, 0])
        def __lt__(self, value): return numpy.ndarray([0, 0])
        def __matmul__(self, value): return numpy.ndarray([0, 0])
        def __mod__(self, value): return numpy.ndarray([0, 0])
        def __mul__(self, value): return numpy.ndarray([0, 0])
        def __ne__(self, value): return numpy.ndarray([0, 0])
        def __neg__(self): return numpy.ndarray([0, 0])
        def __or__(self): return numpy.ndarray([0, 0])
        def __pos__(self): return numpy.ndarray([0, 0])
        def __pow__(self): return numpy.ndarray([0, 0])
        def __repr__(self): return str()
        def __rshift__(self): return numpy.ndarray([0, 0])
        def __setitem__(self, key, value): return uninferable
        def __str__(self): return str()
        def __sub__(self, value): return numpy.ndarray([0, 0])
        def __truediv__(self, value): return numpy.ndarray([0, 0])
        def __xor__(self, value): return numpy.ndarray([0, 0])
        def all(self, axis=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def any(self, axis=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def argmax(self, axis=None, out=None): return np.ndarray([0, 0])
        def argmin(self, axis=None, out=None): return np.ndarray([0, 0])
        def argpartition(self, kth, axis=-1, kind='introselect', order=None): return np.ndarray([0, 0])
        def argsort(self, axis=-1, kind='quicksort', order=None): return np.ndarray([0, 0])
        def astype(self, dtype, order='K', casting='unsafe', subok=True, copy=True): return np.ndarray([0, 0])
        def byteswap(self, inplace=False): return np.ndarray([0, 0])
        def choose(self, choices, out=None, mode='raise'): return np.ndarray([0, 0])
        def clip(self, min=None, max=None, out=None): return np.ndarray([0, 0])
        def compress(self, condition, axis=None, out=None): return np.ndarray([0, 0])
        def conj(self): return np.ndarray([0, 0])
        def conjugate(self): return np.ndarray([0, 0])
        def copy(self, order='C'): return np.ndarray([0, 0])
        def cumprod(self, axis=None, dtype=None, out=None): return np.ndarray([0, 0])
        def cumsum(self, axis=None, dtype=None, out=None): return np.ndarray([0, 0])
        def diagonal(self, offset=0, axis1=0, axis2=1): return np.ndarray([0, 0])
        def dot(self, b, out=None): return np.ndarray([0, 0])
        def dump(self, file): return None
        def dumps(self): return str()
        def fill(self, value): return None
        def flatten(self, order='C'): return np.ndarray([0, 0])
        def getfield(self, dtype, offset=0): return np.ndarray([0, 0])
        def item(self, *args): return uninferable
        def itemset(self, *args): return None
        def max(self, axis=None, out=None): return np.ndarray([0, 0])
        def mean(self, axis=None, dtype=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def min(self, axis=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def newbyteorder(self, new_order='S'): return np.ndarray([0, 0])
        def nonzero(self): return (1,)
        def partition(self, kth, axis=-1, kind='introselect', order=None): return None
        def prod(self, axis=None, dtype=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def ptp(self, axis=None, out=None): return np.ndarray([0, 0])
        def put(self, indices, values, mode='raise'): return None
        def ravel(self, order='C'): return np.ndarray([0, 0])
        def repeat(self, repeats, axis=None): return np.ndarray([0, 0])
        def reshape(self, shape, order='C'): return np.ndarray([0, 0])
        def resize(self, new_shape, refcheck=True): return None
        def round(self, decimals=0, out=None): return np.ndarray([0, 0])
        def searchsorted(self, v, side='left', sorter=None): return np.ndarray([0, 0])
        def setfield(self, val, dtype, offset=0): return None
        def setflags(self, write=None, align=None, uic=None): return None
        def sort(self, axis=-1, kind='quicksort', order=None): return None
        def squeeze(self, axis=None): return np.ndarray([0, 0])
        def std(self, axis=None, dtype=None, out=None, ddof=0, keepdims=False): return np.ndarray([0, 0])
        def sum(self, axis=None, dtype=None, out=None, keepdims=False): return np.ndarray([0, 0])
        def swapaxes(self, axis1, axis2): return np.ndarray([0, 0])
        def take(self, indices, axis=None, out=None, mode='raise'): return np.ndarray([0, 0])
        def tobytes(self, order='C'): return b''
        def tofile(self, fid, sep="", format="%s"): return None
        def tolist(self, ): return []
        def tostring(self, order='C'): return b''
        def trace(self, offset=0, axis1=0, axis2=1, dtype=None, out=None): return np.ndarray([0, 0])
        def transpose(self, *axes): return np.ndarray([0, 0])
        def var(self, axis=None, dtype=None, out=None, ddof=0, keepdims=False): return np.ndarray([0, 0])
        def view(self, dtype=None, type=None): return np.ndarray([0, 0])
    """
    node = astroid.extract_node(ndarray)
    return node.infer(context=context)


def _looks_like_numpy_ndarray(node):
    return isinstance(node, astroid.Attribute) and node.attrname == "ndarray"


astroid.MANAGER.register_transform(
    astroid.Attribute,
    astroid.inference_tip(infer_numpy_ndarray),
    _looks_like_numpy_ndarray,
)
