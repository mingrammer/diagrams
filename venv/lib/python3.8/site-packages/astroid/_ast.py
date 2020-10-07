import ast
from collections import namedtuple
from functools import partial
from typing import Optional
import sys

_ast_py2 = _ast_py3 = None
try:
    import typed_ast.ast3 as _ast_py3
    import typed_ast.ast27 as _ast_py2
except ImportError:
    pass


PY38 = sys.version_info[:2] >= (3, 8)
if PY38:
    # On Python 3.8, typed_ast was merged back into `ast`
    _ast_py3 = ast


FunctionType = namedtuple("FunctionType", ["argtypes", "returns"])


def _get_parser_module(parse_python_two: bool = False):
    if parse_python_two:
        parser_module = _ast_py2
    else:
        parser_module = _ast_py3
    return parser_module or ast


def _parse(string: str, parse_python_two: bool = False):
    parse_module = _get_parser_module(parse_python_two=parse_python_two)
    parse_func = parse_module.parse
    if _ast_py3:
        if PY38:
            parse_func = partial(parse_func, type_comments=True)
        if not parse_python_two:
            parse_func = partial(parse_func, feature_version=sys.version_info.minor)
    return parse_func(string)


def parse_function_type_comment(type_comment: str) -> Optional[FunctionType]:
    """Given a correct type comment, obtain a FunctionType object"""
    if _ast_py3 is None:
        return None

    func_type = _ast_py3.parse(type_comment, "<type_comment>", "func_type")
    return FunctionType(argtypes=func_type.argtypes, returns=func_type.returns)
