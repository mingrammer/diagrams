---
id: edge
title: Edges
---

Edge is an object representing an edge between two Nodes.

## Basic

Node is an abstract concept that represents a single system component object. 

An edge object contains three attributes: **label**, **color** and **style** which mirror corresponding graphviz edge attributes.

```python
from diagrams import Edge
from diagrams.aws.compute import EC2

# line
[EC2("node3"), EC2("node4")] - Edge(color='red', label='label1', style='dotted') - EC2("node")

# list of nodes, one directional
[EC2("node3"), EC2("node4")] >> Edge(color='red', label='label1', style='dotted') >> EC2("node")
[EC2("node3"), EC2("node4")] << Edge(color='green', label='label2', style='dashed') << EC2("node")

# both directional
EC2("node") << Edge(color='blue', label='label3', style='bold') >> EC2("node")

# loop
node = EC2("node")
node >> Edge(color='pink', label='label4', style='solid') << node
```

![custom edges diagram](/img/custom_edges_diagram.png)
