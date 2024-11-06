---
id: installation
title: Installation
---

**diagrams** requires **Python 3.7** or higher, check your Python version first.

**diagrams** uses [Graphviz](https://www.graphviz.org/) to render the diagram, so you need to [install Graphviz](https://graphviz.gitlab.io/download/) to use it.

> macOS users using [Homebrew](https://brew.sh) can install Graphviz via `brew install graphviz` . Similarly, Windows users with [Chocolatey](https://chocolatey.org) installed can run `choco install graphviz`.

After installing Graphviz (or if you already have it), install **diagrams**:

```shell
# using pip (pip3)
$ pip install diagrams

# using pipenv
$ pipenv install diagrams

# using poetry
$ poetry add diagrams
```

## Quick Start

```python
# diagram.py
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Web Service", show=False):
    ELB("lb") >> EC2("web") >> RDS("userdb")
```

To generate the diagram, run:

```shell
$ python diagram.py
```

This generates the diagram below:

![web service diagram](/img/web_service_diagram.png)

It will be saved as `web_service.png` in your working directory.

## Next

See more [Examples](/docs/getting-started/examples) or see the [Guides](/docs/guides/diagram) page for more details.
