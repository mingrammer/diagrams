# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import sys
import astroid

PY37 = sys.version_info >= (3, 7)

if PY37:
    # Since Python 3.7 Hashing Methods are added
    # dynamically to globals()

    def _re_transform():
        return astroid.parse(
            """
        from collections import namedtuple
        _Method = namedtuple('_Method', 'name ident salt_chars total_size')

        METHOD_SHA512 = _Method('SHA512', '6', 16, 106)
        METHOD_SHA256 = _Method('SHA256', '5', 16, 63)
        METHOD_BLOWFISH = _Method('BLOWFISH', 2, 'b', 22)
        METHOD_MD5 = _Method('MD5', '1', 8, 34)
        METHOD_CRYPT = _Method('CRYPT', None, 2, 13)
        """
        )

    astroid.register_module_extender(astroid.MANAGER, "crypt", _re_transform)
