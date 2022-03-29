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

## Jupyter Notebooks

Diagrams can be also rendered directly inside the notebook as like this:

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram") as diag:
    EC2("web")
diag
```

## Options

You can specify the output file format with `outformat` parameter. Default is **png**.

> (png, jpg, svg, pdf and dot) are allowed.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram", outformat="jpg"):
    EC2("web")
```

The `outformat` parameter also support list to output all the defined output in one call.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram Multi Output", outformat=["jpg", "png", "dot"]):
    EC2("web")
```

You can specify the output filename with `filename` parameter. The extension shouldn't be included, it's determined by the `outformat` parameter.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram", filename="my_diagram"):
    EC2("web")
```

You can also disable the automatic file opening by setting the `show` parameter as **false**. Default is **true**.

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Simple Diagram", show=False):
    EC2("web")
```

It allows custom Graphviz dot attributes options.

> `graph_attr`, `node_attr` and `edge_attr` are supported. Here is a [reference link](https://www.graphviz.org/doc/info/attrs.html).

```python
from diagrams import Diagram
from diagrams.aws.compute import EC2

graph_attr = {
	"fontsize": "45",
	"bgcolor": "transparent"
}

with Diagram("Simple Diagram", show=False, graph_attr=graph_attr):
    EC2("web")
```
