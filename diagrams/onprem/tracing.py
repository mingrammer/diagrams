# This module is automatically generated by autogen.sh. DO NOT EDIT.

from . import _OnPrem


class _Tracing(_OnPrem):
    _type = "tracing"
    _icon_dir = "resources/onprem/tracing"


class Jaeger(_Tracing):
    _icon = "jaeger.png"


class Tempo(_Tracing):
    _icon = "tempo.png"


# Aliases
