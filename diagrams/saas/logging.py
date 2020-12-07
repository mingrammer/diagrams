# This module is automatically generated by autogen.sh. DO NOT EDIT.

from . import _Saas


class _Logging(_Saas):
    _type = "logging"
    _icon_dir = "resources/saas/logging"


class Datadog(_Logging):
    _icon = "datadog.png"


class Logdna(_Logging):
    _icon = "logdna.png"


class Loggly(_Logging):
    _icon = "loggly.png"


class Papertrail(_Logging):
    _icon = "papertrail.png"


# Aliases

DataDog = Datadog
