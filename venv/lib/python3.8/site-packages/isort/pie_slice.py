"""pie_slice/overrides.py.

Overrides Python syntax to conform to the Python3 version as much as possible using a '*' import

Copyright (C) 2013  Timothy Edmund Crosley

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""
from __future__ import absolute_import

import collections
import sys

__version__ = "1.1.0"

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
VERSION = sys.version_info

__all__ = ['PY2', 'PY3', 'lru_cache', 'apply_changes_to_python_environment']


if PY3:
    input = input

    def apply_changes_to_python_environment():
        pass
else:
    input = raw_input  # noqa: F821

    python_environment_changes_applied = False

    import sys
    stdout = sys.stdout
    stderr = sys.stderr

    def apply_changes_to_python_environment():
        global python_environment_changes_applied
        if python_environment_changes_applied or sys.getdefaultencoding() == 'utf-8':
            python_environment_changes_applied = True
            return

        try:
            reload(sys)
            sys.stdout = stdout
            sys.stderr = stderr
            sys.setdefaultencoding('utf-8')
        except NameError:  # Python 3
            sys.exit('This should not happen!')

        python_environment_changes_applied = True


if sys.version_info < (3, 2):
    try:
        from threading import Lock
    except ImportError:
        from dummy_threading import Lock

    from functools import wraps

    _CacheInfo = collections.namedtuple("CacheInfo", "hits misses maxsize currsize")

    def lru_cache(maxsize=100):
        """Least-recently-used cache decorator.
        Taking from: https://github.com/MiCHiLU/python-functools32/blob/master/functools32/functools32.py
        with slight modifications.
        If *maxsize* is set to None, the LRU features are disabled and the cache
        can grow without bound.
        Arguments to the cached function must be hashable.
        View the cache statistics named tuple (hits, misses, maxsize, currsize) with
        f.cache_info().  Clear the cache and statistics with f.cache_clear().
        Access the underlying function with f.__wrapped__.
        See: https://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

        """
        def decorating_function(user_function, tuple=tuple, sorted=sorted, len=len, KeyError=KeyError):
            hits, misses = [0], [0]
            kwd_mark = (object(),)          # separates positional and keyword args
            lock = Lock()

            if maxsize is None:
                CACHE = {}

                @wraps(user_function)
                def wrapper(*args, **kwds):
                    key = args
                    if kwds:
                        key += kwd_mark + tuple(sorted(kwds.items()))
                    try:
                        result = CACHE[key]
                        hits[0] += 1
                        return result
                    except KeyError:
                        pass
                    result = user_function(*args, **kwds)
                    CACHE[key] = result
                    misses[0] += 1
                    return result
            else:
                CACHE = collections.OrderedDict()

                @wraps(user_function)
                def wrapper(*args, **kwds):
                    key = args
                    if kwds:
                        key += kwd_mark + tuple(sorted(kwds.items()))
                    with lock:
                        cached = CACHE.get(key, None)
                        if cached:
                            del CACHE[key]
                            CACHE[key] = cached
                            hits[0] += 1
                            return cached
                    result = user_function(*args, **kwds)
                    with lock:
                        CACHE[key] = result     # record recent use of this key
                        misses[0] += 1
                        while len(CACHE) > maxsize:
                            CACHE.popitem(last=False)
                    return result

            def cache_info():
                """Report CACHE statistics."""
                with lock:
                    return _CacheInfo(hits[0], misses[0], maxsize, len(CACHE))

            def cache_clear():
                """Clear the CACHE and CACHE statistics."""
                with lock:
                    CACHE.clear()
                    hits[0] = misses[0] = 0

            wrapper.cache_info = cache_info
            wrapper.cache_clear = cache_clear
            return wrapper

        return decorating_function

else:
    from functools import lru_cache
