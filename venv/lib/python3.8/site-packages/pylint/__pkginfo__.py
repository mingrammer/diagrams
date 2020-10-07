# Copyright (c) 2006-2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2010 Julien Jehannet <julien.jehannet@logilab.fr>
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Ricardo Gemignani <ricardo.gemignani@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2016 Florian Bruhin <git@the-compiler.org>
# Copyright (c) 2016 Jakub Wilk <jwilk@jwilk.net>
# Copyright (c) 2017-2018 Hugo <hugovk@users.noreply.github.com>
# Copyright (c) 2018 Sushobhit <31987769+sushobhit27@users.noreply.github.com>
# Copyright (c) 2018 Ashley Whetter <ashley@awhetter.co.uk>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

# pylint: disable=redefined-builtin,invalid-name
"""pylint packaging information"""

from os.path import join

# For an official release, use dev_version = None
numversion = (2, 4, 4)
dev_version = None

version = ".".join(str(num) for num in numversion)
if dev_version is not None:
    version += "-dev" + str(dev_version)

install_requires = ["astroid>=2.3.0,<2.4", "isort>=4.2.5,<5", "mccabe>=0.6,<0.7"]

dependency_links = []  # type: ignore

extras_require = {}
extras_require[':sys_platform=="win32"'] = ["colorama"]

license = "GPL"
description = "python code static checker"
web = "https://github.com/PyCQA/pylint"
mailinglist = "mailto:code-quality@python.org"
author = "Python Code Quality Authority"
author_email = "code-quality@python.org"

classifiers = [
    "Development Status :: 6 - Mature",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Testing",
]


long_desc = """\
 Pylint is a Python source code analyzer which looks for programming
 errors, helps enforcing a coding standard and sniffs for some code
 smells (as defined in Martin Fowler's Refactoring book)
 .
 Pylint can be seen as another PyChecker since nearly all tests you
 can do with PyChecker can also be done with Pylint. However, Pylint
 offers some more features, like checking length of lines of code,
 checking if variable names are well-formed according to your coding
 standard, or checking if declared interfaces are truly implemented,
 and much more.
 .
 Additionally, it is possible to write plugins to add your own checks.
 .
 Pylint is shipped with "pyreverse" (UML diagram generator)
 and "symilar" (an independent similarities checker)."""

scripts = [
    join("bin", filename) for filename in ("pylint", "symilar", "epylint", "pyreverse")
]
