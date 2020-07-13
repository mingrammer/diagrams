# Changelogs

## 0.16.0

### Breaking Changes

The following import changes:

| Old import path                                    | New import path                                            |
| -------------------------------------------------- | ---------------------------------------------------------- |
| `from diagrams.onprem.logging import Logstash`     | `from diagrams.elastic.elasticsearch import Logstash`      |
| `from diagrams.onprem.monitoring import Kibana`    | `from diagrams.elastic.elasticsearch import Kibana`        |
| `from diagrams.onprem.search import Elasticsearch` | `from diagrams.elastic.elasticsearch import Elasticsearch` |

> The previous icon was the company icon, not the elasticsearch product.
>
> For the company icon: `from diagrams.elastic.saas import Elastic`

### Added

- Docker local development setup: [#210](https://github.com/mingrammer/diagrams/pull/210)
- Support OpenStack [#211](https://github.com/mingrammer/diagrams/pull/211)
- Support SQL, Druid and Databricks
- Support Cloudinary: [#218](https://github.com/mingrammer/diagrams/pull/218)

### Fixed

- Clean GCP resources: [#228](https://github.com/mingrammer/diagrams/pull/228)
- Support DataDog, PaperTrail, Syslog, Rsyslog and Graylog: [#222](https://github.com/mingrammer/diagrams/pull/222)
- Update all OCI icon set (bark and white): [#205](https://github.com/mingrammer/diagrams/pull/205)


## 0.15.0

### Added

- Support curvestyle option (ortho or curved)
- Support Auth0, Cloudflare and Recombee: [#209](https://github.com/mingrammer/diagrams/pull/209)

### Fixed

- Fix typo for PersistentVolume: [#207](https://github.com/mingrammer/diagrams/pull/207)
- Fix misaligned label text position


## 0.14.0

### Added

- Support sagemaker for AWS provider: [#204](https://github.com/mingrammer/diagrams/pull/204)
- Support ConcourseCI: [#198](https://github.com/mingrammer/diagrams/pull/198)
- Support Tekton CLI: [#199](https://github.com/mingrammer/diagrams/pull/199)
- Support more analytics tools for Onprem provider: [#195](https://github.com/mingrammer/diagrams/pull/195)
- Support more resources for AWS provider: [#192](https://github.com/mingrammer/diagrams/pull/192)
- Support kubernetes ecosystem: [#188](https://github.com/mingrammer/diagrams/pull/188)
- Support Beats for ElasticStack provider: [#153](https://github.com/mingrammer/diagrams/pull/153)
- Support more icons for Generic provider: [#186](https://github.com/mingrammer/diagrams/pull/186)
- Support Opsgenie: [#187](https://github.com/mingrammer/diagrams/pull/187)
- Support Tekton: [#150](https://github.com/mingrammer/diagrams/pull/150)
- Support Generic provider: [#171](https://github.com/mingrammer/diagrams/pull/171)


## 0.13.1

### Fixed

- Add missing firebase base class: [3f400a7](https://github.com/mingrammer/diagrams/commit/3f400a7bc3c91ae9db1f2e69c290bc004c6fa4c6)


## 0.13.0

### Added

- Support more DynamoDB and IAM nodes for AWS: [#180](https://github.com/mingrammer/diagrams/pull/180)
- New provider elastic: [#174](https://github.com/mingrammer/diagrams/pull/174)
- Support Rust: [#179](https://github.com/mingrammer/diagrams/pull/179)
- Support Flux and Flagger: [#147](https://github.com/mingrammer/diagrams/pull/147)
- New provider saas: [#173](https://github.com/mingrammer/diagrams/pull/173)
- New provider firebase: [#167](https://github.com/mingrammer/diagrams/pull/167)
- Support ZuulCI: [#145](https://github.com/mingrammer/diagrams/pull/145)


## 0.12.0

### Added

- Support GitlabCI: [#166](https://github.com/mingrammer/diagrams/pull/166)
- Support Sentry: [#165](https://github.com/mingrammer/diagrams/pull/165)
- Support Couchbase: [#164](https://github.com/mingrammer/diagrams/pull/164)
- Support new IoT icons, and new Game, General and Robotics categories for AWS: [#161](https://github.com/mingrammer/diagrams/pull/161)
- Support general icon set for Azure: [#155](https://github.com/mingrammer/diagrams/pull/155)
- Support Fluent Bit: [#154](https://github.com/mingrammer/diagrams/pull/154)
- Support integration services for Azure: [#152](https://github.com/mingrammer/diagrams/pull/152)
- Support custom attribute options for Nodes: [#151](https://github.com/mingrammer/diagrams/pull/151)


## 0.11.0

### Added

- Support programming provider (programming languages and frameworks): [#112](https://github.com/mingrammer/diagrams/pull/112)
- Support NACL, Subnets, Route Table and VPC peering for AWS provider: [#135](https://github.com/mingrammer/diagrams/pull/135)
- Support Loki: [#139](https://github.com/mingrammer/diagrams/pull/139)
- Support Tableau and Metabase: [#142](https://github.com/mingrammer/diagrams/pull/142)
- Support AWS Elemental Services: [#149](https://github.com/mingrammer/diagrams/pull/149)

### Fixed

- Rename Cloudfront to CloudFront: [#129](https://github.com/mingrammer/diagrams/pull/129)


## 0.10.0

### Added

- Support red-colored OCI nodes: [#121](https://github.com/mingrammer/diagrams/pull/121)
- Support custom graph attributes for the Cluster: [6741ed9](https://github.com/mingrammer/diagrams/commit/6741ed9e2bcca297a1044ca5c8f2cf9eb3f8b5b3)


## v0.9.0

### Added

- Support Thanos: [#99](https://github.com/mingrammer/diagrams/pull/99)
- Support AWS VPC Endpoint: [#101](https://github.com/mingrammer/diagrams/pull/101)
- Support AWS VPC Router: [#102](https://github.com/mingrammer/diagrams/pull/102)
- Support Teamcity: [#103](https://github.com/mingrammer/diagrams/pull/103)
- Support Pomerium: [#104](https://github.com/mingrammer/diagrams/pull/104)
- Support Ansible and AWX: [#110](https://github.com/mingrammer/diagrams/pull/110)

### Fixed

- Replace MD5 Hash with UUID: [#94](https://github.com/mingrammer/diagrams/pull/94)
- Verify Edge attributes exist before setting: [#96](https://github.com/mingrammer/diagrams/pull/96)


## v0.8.2

### Added

- Support Diadag: [#88](https://github.com/mingrammer/diagrams/pull/88)
- Support Norika and Embulk: [#87](https://github.com/mingrammer/diagrams/pull/87)


## v0.8.1

### Added

- Support Celery: [#68](https://github.com/mingrammer/diagrams/pull/68)
- Support Terraform: [#79](https://github.com/mingrammer/diagrams/pull/79)
- Support Clickhouse: [#85](https://github.com/mingrammer/diagrams/pull/85)


## v0.8.0

### Added

- Support Apache Beam: [#66](https://github.com/mingrammer/diagrams/pull/66)
- Support PFSense and VyOS: [#67](https://github.com/mingrammer/diagrams/pull/67)
- Support Polyaxon: [#74](https://github.com/mingrammer/diagrams/pull/74)
- Support Spinnaker: [#77](https://github.com/mingrammer/diagrams/pull/77)
- Support Git, GitLab and GitHub of onprem.vcs: [#80](https://github.com/mingrammer/diagrams/pull/80)
- Support Dgraph, JanusGraph and Scylla of onprem.database: [#84](https://github.com/mingrammer/diagrams/pull/84)


## v0.7.4

### Added

- Trivy of onprem.security: [#61](https://github.com/mingrammer/diagrams/pull/61)
- Cloud IAP (Identity-Aware Proxy) for GCP provider: [#56](https://github.com/mingrammer/diagrams/pull/56), [#43](https://github.com/mingrammer/diagrams/pull/43)


## v0.7.3

### Fixed

- Use dynamic keyword attributes for edge init to fix missing attribute


## v0.7.2

### Fixed

- Prevent the edge attrs from overwriting by empty string
- Only use the label for edge


## v0.7.0

### Added

- Customer engagement services for AWS: [#57](https://github.com/mingrammer/diagrams/pull/57)
- Edge attributes support: [#48](https://github.com/mingrammer/diagrams/pull/48)


## v0.6.5

### Added

- More on-prem/aws icons: [#55](https://github.com/mingrammer/diagrams/pull/55)
- Aliases for etcd and haproxy


## v0.6.4

### Added

- AWS management resources

### Fixed

- Update OCI icon set: [#46](https://github.com/mingrammer/diagrams/pull/46)


## v0.6.3

### Added

- Support inline rendering for jupyter notebook


## v0.6.2

### Fixed

- Support multi-line labels


## v0.6.1

### Added

- Aliases for activemq (ActiveMQ) / rabbitmq (RabbitMQ)


## v0.6.0

### Added

- Support custom nodes: [#25](https://github.com/mingrammer/diagrams/pull/25)
- Allow an output filename to be passed to Diagram explicitly: [#28](https://github.com/mingrammer/diagrams/pull/28)
- Support on-premise nodes: [#35](https://github.com/mingrammer/diagrams/pull/35)


## v0.5.0

### Added

- Oracle Cloud provider support: [#20](https://github.com/mingrammer/diagrams/pull/20)


## v0.4.0

### Added

- Alibaba Cloud provider support: [#19](https://github.com/mingrammer/diagrams/pull/19)


## v0.3.0

### Added

- Allow custom dot attributes: [#11](https://github.com/mingrammer/diagrams/pull/11)

### Fixed

- Support Python 3.6: [#13](https://github.com/mingrammer/diagrams/pull/13)


## v0.2.3

### Fixed

- Fix misaligned node labels by removing backward-incompatible 'imagepos' attribute: [#7](https://github.com/mingrammer/diagrams/pull/7)


## v0.2.1

### Added

- Add more AWS analytics services: [870b387](https://github.com/mingrammer/diagrams/commit/870b387ded41cb6591b8bdfd3994e5719d8b9969)


## v0.2.0

### Added

- Support kubernetes diagrams: [3eda1cb](https://github.com/mingrammer/diagrams/commit/3eda1cb6bca8be8a55773d90b93483a8fab3e0f1)
