---
id: custom
title: Custom
---

## Custom with local icons

For this example we use the following architecture:

```
.
├── custom_local.py
├── my_resources
│   ├── cc_heart.black.png
│   ├── cc_attribution.png
│   ├──...
```

The content of custom_local.py file:

```python
from diagrams import Diagram, Cluster
from diagrams.custom import Custom


with Diagram("Custom with local icons\n Can be downloaded here: \nhttps://creativecommons.org/about/downloads/", show=False, filename="custom_local", direction="LR"):
  cc_heart = Custom("Creative Commons", "./my_resources/cc_heart.black.png")
  cc_attribution = Custom("Credit must be given to the creator", "./my_resources/cc_attribution.png")

  cc_sa = Custom("Adaptations must be shared\n under the same terms", "./my_resources/cc_sa.png")
  cc_nd = Custom("No derivatives or adaptations\n of the work are permitted", "./my_resources/cc_nd.png")
  cc_zero = Custom("Public Domain Dedication", "./my_resources/cc_zero.png")

  with Cluster("Non Commercial"):
    non_commercial = [Custom("Y", "./my_resources/cc_nc-jp.png") - Custom("E", "./my_resources/cc_nc-eu.png") - Custom("S", "./my_resources/cc_nc.png")]

  cc_heart >> cc_attribution
  cc_heart >> non_commercial
  cc_heart >> cc_sa
  cc_heart >> cc_nd
  cc_heart >> cc_zero
```

It will generate the following diagram:

![custom local](/img/custom_local.png)


## Custom with remote icons

If your icons are hosted and can be accessed when you generate the diagrams, you can

```python
from diagrams import Diagram, Cluster
from diagrams.custom import Custom
from urllib.request import urlretrieve

with Diagram("Custom with remote icons", show=False, filename="custom_remote", direction="LR"):

  # download the icon image file
  diagrams_url = "https://github.com/mingrammer/diagrams/raw/master/assets/img/diagrams.png"
  diagrams_icon = "diagrams.png"
  urlretrieve(diagrams_url, diagrams_icon)

  diagrams = Custom("Diagrams", diagrams_icon)

  with Cluster("Some Providers"):

    openstack_url = "https://github.com/mingrammer/diagrams/raw/master/resources/openstack/openstack.png"
    openstack_icon = "openstack.png"
    urlretrieve(openstack_url, openstack_icon)

    openstack = Custom("OpenStack", openstack_icon)

    elastic_url = "https://github.com/mingrammer/diagrams/raw/master/resources/elastic/saas/elastic.png"
    elastic_icon = "elastic.png"
    urlretrieve(elastic_url, elastic_icon)

    elastic = Custom("Elastic", elastic_icon)

  diagrams >> openstack
  diagrams >> elastic
```

It will generate the following diagram:

![custom local](/img/custom_remote.png)


Another example can be found [Here](https://diagrams.mingrammer.com/docs/getting-started/examples#rabbitmq-consumers-with-custom-nodes).
