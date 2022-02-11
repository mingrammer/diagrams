

from . import _Splunk


class _Cluster(_Splunk):
    _type = "cluster"
    _icon_dir = "resources/splunk/cluster"

class App(_Cluster):
	_icon = "app.png"

class Deployer(_Cluster):
	_icon = "deployer.png"

class ES(_Cluster):
	_icon = "es.png"

class Forwarder(_Cluster):
	_icon = "forwarder.png"

class HEC(_Cluster):
	_icon = "hec.png"

class LicenseMaster(_Cluster):
	_icon = "license-master.png"

class MasterCluster_node(_Cluster):
	_icon = "master-cluster-node.png"

class Router(_Cluster):
	_icon = "router.png"

class SHCluster(_Cluster):
	_icon = "sh-cluster.png"

class SystemsLinux(_Cluster):
	_icon = "systems-linux.png"

class Bucket(_Cluster):
	_icon = "bucket.png"

class DeploymentServer(_Cluster):
	_icon = "deployment-server.png"

class ESServer(_Cluster):
	_icon = "es-server.png"

class HeavyForwader(_Cluster):
	_icon = "heavy-forwader.png"

class Indexer(_Cluster):
	_icon = "indexer.png"

class LicenseServer(_Cluster):
	_icon = "license-server.png"

class People(_Cluster):
	_icon = "people.png"

class SearchHead(_Cluster):
	_icon = "search-head.png"

class SplunkCloud(_Cluster):
	_icon = "splunk-cloud.png"

class Systems(_Cluster):
	_icon = "systems.png"

class Datastores(_Cluster):
	_icon = "datastores.png"

class Desktop(_Cluster):
	_icon = "desktop.png"

class Firewall(_Cluster):
	_icon = "firewall.png"

class HeavyForwarders(_Cluster):
	_icon = "heavy-forwarders.png"

class Laptop(_Cluster):
	_icon = "laptop.png"

class LogFile(_Cluster):
	_icon = "log-file.png"

class Person(_Cluster):
	_icon = "person.png"

class Search(_Cluster):
	_icon = "search.png"

class SplunkInstance(_Cluster):
	_icon = "splunk-instance.png"

class SystemsWindows(_Cluster):
	_icon = "systems-windows.png"