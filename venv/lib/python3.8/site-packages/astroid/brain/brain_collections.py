# -*- coding: utf-8 -*-
# Copyright (c) 2016, 2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2016-2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2017 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2018 Ioana Tagirta <ioana.tagirta@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import sys

import astroid


def _collections_transform():
    return astroid.parse(
        """
    class defaultdict(dict):
        default_factory = None
        def __missing__(self, key): pass
        def __getitem__(self, key): return default_factory

    """
        + _deque_mock()
        + _ordered_dict_mock()
    )


def _deque_mock():
    base_deque_class = """
    class deque(object):
        maxlen = 0
        def __init__(self, iterable=None, maxlen=None):
            self.iterable = iterable or []
        def append(self, x): pass
        def appendleft(self, x): pass
        def clear(self): pass
        def count(self, x): return 0
        def extend(self, iterable): pass
        def extendleft(self, iterable): pass
        def pop(self): return self.iterable[0]
        def popleft(self): return self.iterable[0]
        def remove(self, value): pass
        def reverse(self): return reversed(self.iterable)
        def rotate(self, n=1): return self
        def __iter__(self): return self
        def __reversed__(self): return self.iterable[::-1]
        def __getitem__(self, index): return self.iterable[index]
        def __setitem__(self, index, value): pass
        def __delitem__(self, index): pass
        def __bool__(self): return bool(self.iterable)
        def __nonzero__(self): return bool(self.iterable)
        def __contains__(self, o): return o in self.iterable
        def __len__(self): return len(self.iterable)
        def __copy__(self): return deque(self.iterable)
        def copy(self): return deque(self.iterable)
        def index(self, x, start=0, end=0): return 0
        def insert(self, x, i): pass
        def __add__(self, other): pass
        def __iadd__(self, other): pass
        def __mul__(self, other): pass
        def __imul__(self, other): pass
        def __rmul__(self, other): pass"""
    return base_deque_class


def _ordered_dict_mock():
    base_ordered_dict_class = """
    class OrderedDict(dict):
        def __reversed__(self): return self[::-1]
        def move_to_end(self, key, last=False): pass"""
    return base_ordered_dict_class


astroid.register_module_extender(astroid.MANAGER, "collections", _collections_transform)
