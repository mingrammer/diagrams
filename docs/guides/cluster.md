---
id: cluster
title: Clusters
---

Cluster allows you group (or clustering) the nodes in an isolated group.

## Basic

Cluster represents a local cluster context.

You can create a cluster context with Cluster class. And you can also connect the nodes in a cluster to other nodes outside a cluster.

```python
from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS
from diagrams.aws.network import Route53

with Diagram("Simple Web Service with DB Cluster", show=False):
    dns = Route53("dns")
    web = ECS("service")

    with Cluster("DB Cluster"):
        db_master = RDS("master")
        db_master - [RDS("slave1"),
                     RDS("slave2")]

    dns >> web >> db_master
```

![simple web service with db cluster diagram](/img/simple_web_service_with_db_cluster_diagram.png)

## Nested Clusters

Nested clustering is also possible.

```python
from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS, EKS, Lambda
from diagrams.aws.database import Redshift
from diagrams.aws.integration import SQS
from diagrams.aws.storage import S3

with Diagram("Event Processing", show=False):
    source = EKS("k8s source")

    with Cluster("Event Flows"):
        with Cluster("Event Workers"):
            workers = [ECS("worker1"),
                       ECS("worker2"),
                       ECS("worker3")]

        queue = SQS("event queue")

        with Cluster("Processing"):
            handlers = [Lambda("proc1"),
                        Lambda("proc2"),
                        Lambda("proc3")]

    store = S3("events store")
    dw = Redshift("analytics")

    source >> workers >> queue >> handlers
    handlers >> store
    handlers >> dw
```

## Clusters with icons in the label

You can add a Node icon before the cluster label (and specify its size as well).  You need to import the used Node class first.

```python
from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS, Aurora
from diagrams.aws.network import Route53, VPC

with Diagram("Simple Web Service with DB Cluster", show=False):
    dns = Route53("dns")
    web = ECS("service")

    with Cluster(label='VPC',icon=VPC):
        with Cluster("DB Cluster",icon=Aurora,icon_size=30):
            db_master = RDS("master")
            db_master - [RDS("slave1"),
                         RDS("slave2")]

        dns >> web >> db_master
```

![event processing diagram](/img/event_processing_diagram.png)

> There is no depth limit of nesting. Feel free to create nested clusters as deep as you want.
