---
id: cluster
title: Clusters
---

`Cluster` allows you to group (or cluster) nodes in an isolated group.

## Basic

`Cluster` represents a local cluster context.

You can create a cluster context using the `Cluster` class. You can also connect the nodes in a cluster to other nodes outside a cluster.

```python
from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS
from diagrams.aws.network import Route53

with Diagram("Simple Web Service with DB Cluster", show=False):
    dns = Route53("dns")
    web = ECS("service")

    with Cluster("DB Cluster"):
        db_primary = RDS("primary")
        db_primary - [RDS("replica1"),
                     RDS("replica2")]

    dns >> web >> db_primary
```

![simple web service with db cluster diagram](/img/simple_web_service_with_db_cluster_diagram.png)

## Nested Clusters

Nested clustering is also possible:

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

![event processing diagram](/img/event_processing_diagram.png)

> There is no depth limit to nesting. Feel free to create nested clusters as deep as you want.
