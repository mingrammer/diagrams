from diagrams import Cluster, Diagram
from diagrams.ibm.network import Loadbalancer
from diagrams.ibm.network import Vpc
from diagrams.ibm.compute import Instance
from diagrams.ibm.general import MonitoringLogging

with Diagram("Network", show=True):
    with Cluster("Services"):
        svc_group = [Instance("web1"),
                     Instance("web2"),
                     Instance("web3")] 

    Vpc("vpc") >> Loadbalancer("lb") >> svc_group 

    svc_group >> MonitoringLogging("logdna")
