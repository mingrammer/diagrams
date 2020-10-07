# -*- coding: utf-8 -*-
# Copyright (c) 2006-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2009 Vincent
# Copyright (c) 2009 Mads Kiilerich <mads@kiilerich.com>
# Copyright (c) 2012-2014 Google, Inc.
# Copyright (c) 2014-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014-2015 Michal Nowikowski <godfryd@gmail.com>
# Copyright (c) 2014 LCD 47 <lcd047@gmail.com>
# Copyright (c) 2014 Brett Cannon <brett@python.org>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2014 Damien Nozay <damien.nozay@gmail.com>
# Copyright (c) 2015 Aru Sahni <arusahni@gmail.com>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2015 Simu Toni <simutoni@gmail.com>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2016 Glenn Matthews <glenn@e-dad.net>
# Copyright (c) 2016 Glenn Matthews <glmatthe@cisco.com>
# Copyright (c) 2016 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2016 xmo-odoo <xmo-odoo@users.noreply.github.com>
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017 Pierre Sassoulas <pierre.sassoulas@cea.fr>
# Copyright (c) 2017 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2017 Chris Lamb <chris@chris-lamb.co.uk>
# Copyright (c) 2017 Anthony Sottile <asottile@umich.edu>
# Copyright (c) 2017 Thomas Hisch <t.hisch@gmail.com>
# Copyright (c) 2017 Mikhail Fesenko <proggga@gmail.com>
# Copyright (c) 2017 Craig Citro <craigcitro@gmail.com>
# Copyright (c) 2017 Ville Skyttä <ville.skytta@iki.fi>
# Copyright (c) 2018 ssolanki <sushobhitsolanki@gmail.com>
# Copyright (c) 2018 Sushobhit <31987769+sushobhit27@users.noreply.github.com>
# Copyright (c) 2018 Pierre Sassoulas <pierre.sassoulas@wisebim.fr>
# Copyright (c) 2018 Reverb C <reverbc@users.noreply.github.com>
# Copyright (c) 2018 Nick Drozd <nicholasdrozd@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""some various utilities and helper classes, most of them used in the
main pylint class
"""

from pylint.utils.ast_walker import ASTWalker
from pylint.utils.file_state import FileState
from pylint.utils.utils import (
    _basename_in_blacklist_re,
    _check_csv,
    _format_option_value,
    _splitstrip,
    _unquote,
    decoding_stream,
    deprecated_option,
    expand_modules,
    format_section,
    get_global_option,
    get_module_and_frameid,
    get_rst_section,
    get_rst_title,
    normalize_text,
    register_plugins,
    safe_decode,
    tokenize_module,
)
