"""
This module contains deprecation messages and bits of code used elsewhere in the codebase
that is planned to be removed in the next pytest release.

Keeping it in a central location makes it easy to track what is deprecated and should
be removed when the time comes.

All constants defined in this module should be either PytestWarning instances or UnformattedWarning
in case of warnings which need to format their messages.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from _pytest.warning_types import PytestDeprecationWarning
from _pytest.warning_types import RemovedInPytest4Warning
from _pytest.warning_types import UnformattedWarning


MAIN_STR_ARGS = RemovedInPytest4Warning(
    "passing a string to pytest.main() is deprecated, "
    "pass a list of arguments instead."
)

YIELD_TESTS = RemovedInPytest4Warning(
    "yield tests are deprecated, and scheduled to be removed in pytest 4.0"
)

CACHED_SETUP = RemovedInPytest4Warning(
    "cached_setup is deprecated and will be removed in a future release. "
    "Use standard fixture functions instead."
)

COMPAT_PROPERTY = UnformattedWarning(
    RemovedInPytest4Warning,
    "usage of {owner}.{name} is deprecated, please use pytest.{name} instead",
)

CUSTOM_CLASS = UnformattedWarning(
    RemovedInPytest4Warning,
    'use of special named "{name}" objects in collectors of type "{type_name}" to '
    "customize the created nodes is deprecated. "
    "Use pytest_pycollect_makeitem(...) to create custom "
    "collection nodes instead.",
)

FUNCARG_PREFIX = UnformattedWarning(
    RemovedInPytest4Warning,
    '{name}: declaring fixtures using "pytest_funcarg__" prefix is deprecated '
    "and scheduled to be removed in pytest 4.0.  "
    "Please remove the prefix and use the @pytest.fixture decorator instead.",
)

FIXTURE_FUNCTION_CALL = UnformattedWarning(
    RemovedInPytest4Warning,
    'Fixture "{name}" called directly. Fixtures are not meant to be called directly, '
    "are created automatically when test functions request them as parameters. "
    "See https://docs.pytest.org/en/latest/fixture.html for more information.",
)

FIXTURE_NAMED_REQUEST = PytestDeprecationWarning(
    "'request' is a reserved name for fixtures and will raise an error in future versions"
)

CFG_PYTEST_SECTION = UnformattedWarning(
    RemovedInPytest4Warning,
    "[pytest] section in {filename} files is deprecated, use [tool:pytest] instead.",
)

GETFUNCARGVALUE = RemovedInPytest4Warning(
    "getfuncargvalue is deprecated, use getfixturevalue"
)

RESULT_LOG = RemovedInPytest4Warning(
    "--result-log is deprecated and scheduled for removal in pytest 4.0.\n"
    "See https://docs.pytest.org/en/latest/usage.html#creating-resultlog-format-files for more information."
)

MARK_INFO_ATTRIBUTE = RemovedInPytest4Warning(
    "MarkInfo objects are deprecated as they contain merged marks which are hard to deal with correctly.\n"
    "Please use node.get_closest_marker(name) or node.iter_markers(name).\n"
    "Docs: https://docs.pytest.org/en/latest/mark.html#updating-code"
)

MARK_PARAMETERSET_UNPACKING = RemovedInPytest4Warning(
    "Applying marks directly to parameters is deprecated,"
    " please use pytest.param(..., marks=...) instead.\n"
    "For more details, see: https://docs.pytest.org/en/latest/parametrize.html"
)

NODE_WARN = RemovedInPytest4Warning(
    "Node.warn(code, message) form has been deprecated, use Node.warn(warning_instance) instead."
)

RECORD_XML_PROPERTY = RemovedInPytest4Warning(
    'Fixture renamed from "record_xml_property" to "record_property" as user '
    "properties are now available to all reporters.\n"
    '"record_xml_property" is now deprecated.'
)

COLLECTOR_MAKEITEM = RemovedInPytest4Warning(
    "pycollector makeitem was removed as it is an accidentially leaked internal api"
)

METAFUNC_ADD_CALL = RemovedInPytest4Warning(
    "Metafunc.addcall is deprecated and scheduled to be removed in pytest 4.0.\n"
    "Please use Metafunc.parametrize instead."
)

PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST = RemovedInPytest4Warning(
    "Defining pytest_plugins in a non-top-level conftest is deprecated, "
    "because it affects the entire directory tree in a non-explicit way.\n"
    "Please move it to the top level conftest file instead."
)

PYTEST_NAMESPACE = RemovedInPytest4Warning(
    "pytest_namespace is deprecated and will be removed soon"
)

PYTEST_ENSURETEMP = RemovedInPytest4Warning(
    "pytest/tmpdir_factory.ensuretemp is deprecated, \n"
    "please use the tmp_path fixture or tmp_path_factory.mktemp"
)
