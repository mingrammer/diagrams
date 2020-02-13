---
id: diagram
title: Diagrams
---

Diagram is a primary object representing a diagram.

## Basic

Diagram represents a global diagram context.

You can create a diagram context with Diagram class. The first parameter of Diagram constructor will be used for output filename.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram"):
    EC2("web")
```

And if you run the above script with below command,

```shell
$ python diagram.py
```

It will generate an image file with single `EC2` node drawn as `simple_diagram.png` on your working directory, and open that created image file immediately.

## Options

You can specify the output file format with `outformat` parameter. Default is **png**.

> (png, jpg, svg, and pdf) are allowed.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram", outformat="jpg"):
    EC2("web")
```

You can also disable the automatic file opening by setting the `show` parameter as **false**. Default is **true**.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram", show=False):
    EC2("web")
```

If you are familiar with Graphviz, you can customize the diagrams with Graphviz attribute config options.

> `graph_attr`, `node_attr` and `edge_attr` are allowed. Here is a [reference link](https://www.graphviz.org/doc/info/attrs.html).

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

graph_attr = {
	"fontsize": 45,
  "bgcolor": "transparent"
}

with Diagram("Simple Diagram", show=False, graph_attr=graph_attr):
    EC2("web")
```
