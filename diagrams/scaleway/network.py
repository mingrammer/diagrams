# This module is automatically generated by autogen.sh. DO NOT EDIT.

from . import _Scaleway


class _Network(_Scaleway):
    _type = "network"
    _icon_dir = "resources/scaleway/network"


class Cdn(_Network):
    _icon = "cdn.png"


class DirectConnect(_Network):
    _icon = "direct-connect.png"


class Dns(_Network):
    _icon = "dns.png"


class LoadBalancers(_Network):
    _icon = "load-balancers.png"


class PrivateNetworks(_Network):
    _icon = "private-networks.png"


class PublicGateway(_Network):
    _icon = "public-gateway.png"


class Vpc(_Network):
    _icon = "vpc.png"


# Aliases
