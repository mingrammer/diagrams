![diagrams logo](assets/img/diagrams.png)

# Diagrams

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)
[![pypi version](https://badge.fury.io/py/diagrams.svg)](https://badge.fury.io/py/diagrams)
![python version](https://img.shields.io/badge/python-3.6%2C3.7%2C3.8-blue?logo=python)
![Run tests](https://github.com/mingrammer/diagrams/workflows/Run%20tests/badge.svg?branch=master)
[![todos](https://badgen.net/https/api.tickgit.com/badgen/github.com/mingrammer/diagrams?label=todos)](https://www.tickgit.com/browse?repo=github.com/mingrammer/diagrams)

![on premise provider](https://img.shields.io/badge/provider-OnPremise-orange?color=5f87bf)
![aws provider](https://img.shields.io/badge/provider-AWS-orange?logo=amazon-aws&color=ff9900)
![azure provider](https://img.shields.io/badge/provider-Azure-orange?logo=microsoft-azure&color=0089d6)
![gcp provider](https://img.shields.io/badge/provider-GCP-orange?logo=google-cloud&color=4285f4)
![kubernetes provider](https://img.shields.io/badge/provider-Kubernetes-orange?logo=kubernetes&color=326ce5)
![alibaba cloud provider](https://img.shields.io/badge/provider-AlibabaCloud-orange)
![oracle cloud provider](https://img.shields.io/badge/provider-OracleCloud-orange?logo=oracle&color=f80000)
![openstack provider](https://img.shields.io/badge/provider-OpenStack-orange?logo=openstack&color=da1a32)
![firebase provider](https://img.shields.io/badge/provider-Firebase-orange?logo=firebase&color=FFCA28)
![outscale provider](https://img.shields.io/badge/provider-OutScale-orange?color=5f87bf)
![elastic provider](https://img.shields.io/badge/provider-Elastic-orange?logo=elastic&color=005571)
![generic provider](https://img.shields.io/badge/provider-Generic-orange?color=5f87bf)
![programming provider](https://img.shields.io/badge/provider-Programming-orange?color=5f87bf)
![saas provider](https://img.shields.io/badge/provider-SaaS-orange?color=5f87bf)

<a href="https://www.buymeacoffee.com/mingrammer" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

**Diagram as Code**.

Diagrams lets you draw the cloud system architecture **in Python code**. It was born for **prototyping** a new system architecture design without any design tools. You can also describe or visualize the existing system architecture as well. Diagrams currently supports main major providers including: `AWS`, `Azure`, `GCP`, `Kubernetes`, `Alibaba Cloud`, `Oracle Cloud` etc... It also supports `On-Premise` nodes, `SaaS` and major `Programming` frameworks and languages.

**Diagram as Code** also allows you to **track** the architecture diagram changes in any **version control** system.

>  NOTE: It does not control any actual cloud resources nor does it generate cloud formation or terraform code. It is just for drawing the cloud system architecture diagrams.

## Getting Started

It requires **Python 3.6** or higher, check your Python version first.

It uses [Graphviz](https://www.graphviz.org/) to render the diagram, so you need to [install Graphviz](https://graphviz.gitlab.io/download/) to use **diagrams**. After installing graphviz (or already have it), install the **diagrams**.

> macOS users can download the Graphviz via `brew install graphviz` if you're using [Homebrew](https://brew.sh).

```shell
# using pip (pip3)
$ pip install diagrams

# using pipenv
$ pipenv install diagrams

# using poetry
$ poetry add diagrams
```

You can start with [quick start](https://diagrams.mingrammer.com/docs/getting-started/installation#quick-start). Check out [guides](https://diagrams.mingrammer.com/docs/guides/diagram) for more details, and you can find all available nodes list in [here](https://diagrams.mingrammer.com/docs/nodes/aws).

## Examples

| Event Processing                                             | Stateful Architecture                                        | Advanced Web Service                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![event processing](https://diagrams.mingrammer.com/img/event_processing_diagram.png) | ![stateful architecture](https://diagrams.mingrammer.com/img/stateful_architecture_diagram.png) | ![advanced web service with on-premise](https://diagrams.mingrammer.com/img/advanced_web_service_with_on-premise.png) |

You can find all the examples on the [examples](https://diagrams.mingrammer.com/docs/getting-started/examples) page.

## Contributing

To contribute to diagram, check out [contribution guidelines](CONTRIBUTING.md).

> Let me know if you are using diagrams! I'll add you in showcase page. (I'm working on it!) :)

## Who uses it?

[![GitPitch](https://gitpitch.com/gpimg/logo.png)](https://gitpitch.com/)

[GitPitch](https://gitpitch.com/) is the perfect slide deck solution for Tech Conferences, Training, Developer Advocates, and Educators. Diagrams is now available as a dedicated [Cloud Diagram Markdown Widget](https://docs.gitpitch.com/#/diagrams/cloud-architecture) so you can use Diagrams directly on any slide for conferences, meetups, and training.

[Cloudiscovery](https://github.com/Cloud-Architects/cloudiscovery) helps you to analyze resources in your cloud (AWS/GCP/Azure/Alibaba/IBM) account. It allows you to create a diagram of analyzed cloud resource map based on this Diagrams library, so you can draw the your existing cloud infrastructure with Cloudicovery.

[Airflow Diagrams](https://github.com/feluelle/airflow-diagrams) is an Airflow plugin that aims to easily visualise your Airflow DAGs on service level from providers like AWS, GCP, Azure, etc. via diagrams.

## Other languages

- If you are familiar to Go, you can use [go-diagrams](https://github.com/blushft/go-diagrams) as well.

## License

[MIT](LICENSE)
