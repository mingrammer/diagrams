# Copyright (c) 2008, 2012 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014, 2016-2017 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import sys

from pylint.__pkginfo__ import version as __version__
from pylint.checkers.similar import Run as SimilarRun
from pylint.epylint import Run as EpylintRun
from pylint.lint import Run as PylintRun
from pylint.pyreverse.main import Run as PyreverseRun


def run_pylint():
    """run pylint"""

    try:
        PylintRun(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(1)


def run_epylint():
    """run pylint"""

    EpylintRun()


def run_pyreverse():
    """run pyreverse"""

    PyreverseRun(sys.argv[1:])


def run_symilar():
    """run symilar"""

    SimilarRun(sys.argv[1:])
