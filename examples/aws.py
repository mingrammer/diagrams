from diagrams import Diagram, Edge
from diagrams.aws.cluster import *
from diagrams.aws.compute import EC2
from diagrams.onprem.container import Docker
from diagrams.onprem.cluster import *
from diagrams.aws.network import ELB

with Diagram(name="", direction="TB", show=True):
    with Cluster("AWS"):
        with Region("eu-west-1"):
            with AvailabilityZone("eu-west-1a"):
                with VirtualPrivateCloud(""):
                    with PrivateSubnet("Private"):
                        with SecurityGroup("web sg"):
                            with AutoScalling(""):
                                with EC2Contents("A"):
                                    d1 = Docker("Container")
                                with ServerContents("A1"):
                                    d2 = Docker("Container")

                    with PublicSubnet("Public"):
                        with SecurityGroup("elb sg"):
                            lb = ELB()

    lb >> Edge(forward=True, reverse=True) >> d1
    lb >> Edge(forward=True, reverse=True) >> d2
