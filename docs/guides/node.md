---
id: node
title: Nodes
---

Node is a second object representing a node or system component.

## Basic

Node is an abstract concept that represents a single system component object. 

A node object consists of three parts: **provider**, **resource type** and **name**. You may already have seen each part in the previous example.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram"):
    EC2("web")
```

In above example, the `EC2` is a node of `compute` resource type which provided by `aws` provider.

You can use other node objects in a similar manner like:

```python
# aws resources
from diagrams.aws.compute import ECS, Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ELB, Route53, VPC
...

# azure resources
from diagrams.azure.compute import FunctionApps
from diagrams.azure.storage import BlobStorage
...

# alibaba cloud resources
from diagrams.alibabacloud.compute import ECS
from diagrams.alibabacloud.storage import ObjectTableStore
...

# gcp resources
from diagrams.gcp.compute import AppEngine, GKE
from diagrams.gcp.ml import AutoML 
...

# k8s resources
from diagrams.k8s.compute import Pod, StatefulSet
from diagrams.k8s.network import Service
from diagrams.k8s.storage import PV, PVC, StorageClass
...

# oracle resources
from diagrams.oci.compute import VirtualMachine, Container
from diagrams.oci.network import Firewall
from diagrams.oci.storage import FileStorage, StorageGateway
```

You can find all available nodes list in [Here](https://diagrams.mingrammer.com/docs/nodes/aws).

## Data Flow

You can represent data flow by connecting the nodes with these operators: `>>`, `<<` and `-`.

* **>>**: Connect nodes in left to right direction. 
* **<<**: Connect nodes in right to left direction.
* **-**: Connect nodes in no direction. Undirected.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.aws.storage import S3

with Diagram("Web Services", show=False):
    ELB("lb") >> EC2("web") >> RDS("userdb") >> S3("store")
    ELB("lb") >> EC2("web") >> RDS("userdb") << EC2("stat")
    (ELB("lb") >> EC2("web")) - EC2("web") >> RDS("userdb")
```

> Be careful when using the `-` and any shift operators together, which could cause unexpected results due to operator precedence. 

![web services diagram](/img/web_services_diagram.png)

> The order of rendered diagrams is the reverse of the declaration order.

You can change the data flow direction with `direction` parameter. Default is **LR**.

> (TB, BT, LR and RL) are allowed.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Workers", show=False, direction="TB"):
    lb = ELB("lb")
    db = RDS("events")
    lb >> EC2("worker1") >> db
    lb >> EC2("worker2") >> db
    lb >> EC2("worker3") >> db
    lb >> EC2("worker4") >> db
    lb >> EC2("worker5") >> db
```

![workers diagram](/img/workers_diagram.png)

## Group Data Flow

Above worker example has too many redundant flows. In this case, you can group nodes into a list so that all nodes are connected to other nodes at once.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Grouped Workers", show=False, direction="TB"):
    ELB("lb") >> [EC2("worker1"),
                  EC2("worker2"),
                  EC2("worker3"),
                  EC2("worker4"),
                  EC2("worker5")] >> RDS("events")
```

![grouped workers diagram](/img/grouped_workers_diagram.png)

> You can't connect two **lists** directly because shift/arithmetic operations between lists are not allowed in Python.
