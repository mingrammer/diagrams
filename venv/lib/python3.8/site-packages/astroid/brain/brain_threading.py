# -*- coding: utf-8 -*-
# Copyright (c) 2016 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import astroid


def _thread_transform():
    return astroid.parse(
        """
    class lock(object):
        def acquire(self, blocking=True, timeout=-1):
            pass
        def release(self):
            pass
        def __enter__(self):
            return True
        def __exit__(self, *args):
            pass
        def locked(self):
            return False

    def Lock():
        return lock()
    """
    )


astroid.register_module_extender(astroid.MANAGER, "threading", _thread_transform)
