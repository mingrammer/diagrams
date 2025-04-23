---
id: edge
title: Edges
---

`Edge` represents an edge between nodes.

## Basic

`Edge` is an object representing a connection between nodes with some additional properties.

An edge object contains three attributes: **label**, **color**, and **style**. They mirror the corresponding Graphviz edge attributes.

```python
from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.analytics import Spark
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.aggregator import Fluentd
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.network import Nginx
from diagrams.onprem.queue import Kafka

with Diagram(name="Advanced Web Service with On-Premises (colored)", show=False):
    ingress = Nginx("ingress")

    metrics = Prometheus("metric")
    metrics << Edge(color="firebrick", style="dashed") << Grafana("monitoring")

    with Cluster("Service Cluster"):
        grpcsvc = [
            Server("grpc1"),
            Server("grpc2"),
            Server("grpc3")]

    with Cluster("Sessions HA"):
        primary = Redis("session")
        primary \
            - Edge(color="brown", style="dashed") \
            - Redis("replica") \
            << Edge(label="collect") \
            << metrics
        grpcsvc >> Edge(color="brown") >> primary

    with Cluster("Database HA"):
        primary = PostgreSQL("users")
        primary \
            - Edge(color="brown", style="dotted") \
            - PostgreSQL("replica") \
            << Edge(label="collect") \
            << metrics
        grpcsvc >> Edge(color="black") >> primary

    aggregator = Fluentd("logging")
    aggregator \
        >> Edge(label="parse") \
        >> Kafka("stream") \
        >> Edge(color="black", style="bold") \
        >> Spark("analytics")

    ingress \
        >> Edge(color="darkgreen") \
        << grpcsvc \
        >> Edge(color="darkorange") \
        >> aggregator
```
![advanced web service with on-premise diagram colored](/img/advanced_web_service_with_on-premise_colored.png)

## Less Edges

As you can see on the previous graph the edges can quickly become noisy. Below are two examples to solve this problem.

One approach is to get creative with the Node class to create blank placeholders, together with named nodes within Clusters, and then only pointing to single named elements within those Clusters.

Compare the output below to the example output above .

```python
from diagrams import Cluster, Diagram, Node
from diagrams.onprem.analytics import Spark
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.aggregator import Fluentd
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.network import Nginx
from diagrams.onprem.queue import Kafka

with Diagram("\nAdvanced Web Service with On-Premise Less edges", show=False) as diag:
    ingress = Nginx("ingress")

    with Cluster("Service Cluster"):
        serv1 = Server("grpc1")
        serv2 = Server("grpc2")
        serv3 = Server("grpc3")

    with Cluster(""):
        blankHA = Node("", shape="plaintext", width="0", height="0")

        metrics = Prometheus("metric")
        metrics << Grafana("monitoring")

        aggregator = Fluentd("logging")
        blankHA >> aggregator >> Kafka("stream") >> Spark("analytics")

        with Cluster("Database HA"):
            db = PostgreSQL("users")
            db - PostgreSQL("replica") << metrics
            blankHA >> db

        with Cluster("Sessions HA"):
            sess = Redis("session")
            sess - Redis("replica") << metrics
            blankHA >> sess

    ingress >> serv2 >> blankHA

diag
```

![advanced web service with on-premise less edges](/img/advanced_web_service_with_on-premise_less_edges.png)

## Merged Edges

Yet another option is to set the graph_attr dictionary key "concentrate" to "true".

Note the following restrictions:

1.  the Edge must end at the same headport
2.  This only works when the "splines" graph_attr key is set to the value "spline". It has no effect when the value was set to "ortho", which is the default for the diagrams library.
3. this will only work with the "dot" layout engine, which is the default for the diagrams library.

For more information see:

  https://graphviz.gitlab.io/doc/info/attrs.html#d:concentrate

  https://www.graphviz.org/pdf/dotguide.pdf Section 3.3 Concentrators



```python
from diagrams import Cluster, Diagram, Edge, Node
from diagrams.onprem.analytics import Spark
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.aggregator import Fluentd
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.network import Nginx
from diagrams.onprem.queue import Kafka

graph_attr = {
    "concentrate": "true",
    "splines": "spline",
}

edge_attr = {
    "minlen":"3",
}

with Diagram("\n\nAdvanced Web Service with On-Premise Merged edges", show=False,
            graph_attr=graph_attr,
            edge_attr=edge_attr) as diag:

    ingress = Nginx("ingress")

    metrics = Prometheus("metric")
    metrics << Edge(minlen="0") << Grafana("monitoring")

    with Cluster("Service Cluster"):
        grpsrv = [
            Server("grpc1"),
            Server("grpc2"),
            Server("grpc3")]

    blank = Node("", shape="plaintext", height="0.0", width="0.0")

    with Cluster("Sessions HA"):
        sess = Redis("session")
        sess - Redis("replica") << metrics

    with Cluster("Database HA"):
        db = PostgreSQL("users")
        db - PostgreSQL("replica") << metrics

    aggregator = Fluentd("logging")
    aggregator >> Kafka("stream") >> Spark("analytics")

    ingress >> [grpsrv[0], grpsrv[1], grpsrv[2],]
    [grpsrv[0], grpsrv[1], grpsrv[2],] - Edge(headport="w", minlen="1") - blank
    blank >> Edge(headport="w", minlen="2") >> [sess, db, aggregator]

diag
```
![advanced web service with on-premise merged edges](/img/advanced_web_service_with_on-premise_merged_edges.png)