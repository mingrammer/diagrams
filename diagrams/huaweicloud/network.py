# This module is automatically generated by autogen.sh. DO NOT EDIT.

from . import _Huaweicloud


class _Network(_Huaweicloud):
    _type = "network"
    _icon_dir = "resources/huaweicloud/network"


class DirectConnect(_Network):
    _icon = "direct-connect.png"


class DomainNameService(_Network):
    _icon = "domain-name-service.png"


class ElasticIp(_Network):
    _icon = "elastic-ip.png"


class ElasticLoadBalance(_Network):
    _icon = "elastic-load-balance.png"


class NatGateway(_Network):
    _icon = "nat-gateway.png"


class VirtualPrivateCloud(_Network):
    _icon = "virtual-private-cloud.png"


class VirtualPrivateNetwork(_Network):
    _icon = "virtual-private-network.png"


# Aliases

ELB = ElasticLoadBalance
VPC = VirtualPrivateCloud
DNS = DomainNameService
DC = DirectConnect
NAT = NatGateway
EIP = ElasticIp
VPC = VirtualPrivateNetwork
