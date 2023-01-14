from diagrams import Diagram, Edge
from diagrams.azure.cluster import *
from diagrams.azure.compute import VM
from diagrams.onprem.container import Docker
from diagrams.onprem.cluster import *
from diagrams.azure.network import LoadBalancers

with Diagram(name="", filename="azure", direction="TB", show=True):
    with Cluster("Azure"):
        with Region("East US2"):
            with AvailabilityZone("Zone 2"):
                with VirtualNetwork(""):
                    with SubnetWithNSG("Private"):
                        # with VMScaleSet(""): # Depends on PR-404
                        with VMContents("A"):
                            d1 = Docker("Container")
                        with ServerContents("A1"):
                            d2 = Docker("Container")

                    with Subnet("Public"):
                        lb = LoadBalancers()

    lb >> Edge(forward=True, reverse=True) >> d1
    lb >> Edge(forward=True, reverse=True) >> d2
