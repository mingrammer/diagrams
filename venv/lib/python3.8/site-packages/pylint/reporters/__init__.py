# -*- coding: utf-8 -*-
# Copyright (c) 2006, 2010, 2012-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2012 FELD Boris <lothiraldan@gmail.com>
# Copyright (c) 2014-2017 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Ricardo Gemignani <ricardo.gemignani@gmail.com>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015 Simu Toni <simutoni@gmail.com>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2017 Kári Tristan Helgason <kthelgason@gmail.com>
# Copyright (c) 2018 ssolanki <sushobhitsolanki@gmail.com>
# Copyright (c) 2018 Sushobhit <31987769+sushobhit27@users.noreply.github.com>
# Copyright (c) 2018 Ville Skyttä <ville.skytta@upcloud.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""utilities methods and classes for reporters"""


from pylint import utils
from pylint.reporters.base_reporter import BaseReporter
from pylint.reporters.collecting_reporter import CollectingReporter
from pylint.reporters.json_reporter import JSONReporter
from pylint.reporters.reports_handler_mix_in import ReportsHandlerMixIn


def initialize(linter):
    """initialize linter with reporters in this package """
    utils.register_plugins(linter, __path__[0])


__all__ = ["BaseReporter", "ReportsHandlerMixIn", "JSONReporter", "CollectingReporter"]
