
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("test_2", show=False, direction="TB"):
    ELB("lb") >> [EC2("ワーカー１"),
                  EC2("작업자 2를"),
                  EC2("робітник 3"),
                  EC2("worker4"),
                  EC2("työntekijä 4")] >> RDS("events")
