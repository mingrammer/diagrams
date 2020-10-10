# Changelogs

## 0.17.0

### Added

- Support GCP Endpoints: [#259](https://github.com/mingrammer/diagrams/pull/259)
- Support DroneCI and Atlantis (Terraform): [#255](https://github.com/mingrammer/diagrams/pull/255)
- Support Okta: [#254](https://github.com/mingrammer/diagrams/pull/254)
- Support OutScale provider: [#251](https://github.com/mingrammer/diagrams/pull/251)
- Support Prometheus Operator: [#253](https://github.com/mingrammer/diagrams/pull/253)
- Support Snowflake: [#245](https://github.com/mingrammer/diagrams/pull/245)
- Support for CJK fonts + Replace ms-fonts with opensans: [#242](https://github.com/mingrammer/diagrams/pull/242)
- Support Pushover: [#241](https://github.com/mingrammer/diagrams/pull/241)

### Fixed

- Update bm, vm cases for OCI
- Set a dummy filename to prevent raise error when both name and filename are not provided: [#240](https://github.com/mingrammer/diagrams/pull/240)

## 0.16.0

### Breaking Changes

The following import changes:

#### Elastic

| Old import path                                                    | New import path                                               |
| -------------------------------------------------------------------| --------------------------------------------------------------|
| `from diagrams.onprem.logging import Logstash`                     | `from diagrams.elastic.elasticsearch import Logstash`         |
| `from diagrams.onprem.monitoring import Kibana`                    | `from diagrams.elastic.elasticsearch import Kibana`           |
| `from diagrams.onprem.search import Elasticsearch`                 | `from diagrams.elastic.elasticsearch import Elasticsearch`    |

> About `from diagrams.onprem.search import Elasticsearch` the previous icon was the company icon, not the elasticsearch product.
>
> For the company icon use: `from diagrams.elastic.saas import Elastic`

#### OCI

| Old import path                                                    | New import path                                               |
| -------------------------------------------------------------------| --------------------------------------------------------------|
| `from diagrams.oci.compute import AutoScale`                       | `from diagrams.oci.compute import Autoscale`                  |
| `from diagrams.oci.compute import AutoScaleWhite`                  | `from diagrams.oci.compute import AutoscaleWhite`             |
| `from diagrams.oci.compute import Bm`                              | `from diagrams.oci.compute import BM`                         |
| `from diagrams.oci.compute import BmWhite`                         | `from diagrams.oci.compute import BMWhite`                    |
| `from diagrams.oci.compute import Vm`                              | `from diagrams.oci.compute import VM`                         |
| `from diagrams.oci.compute import VmWhite`                         | `from diagrams.oci.compute import VMWhite`                    |
| `from diagrams.oci.connectivity import Customerdatacenter`         | `from diagrams.oci.connectivity import CustomerDatacenter`    |
| `from diagrams.oci.connectivity import CustomerdatacenterWhite`    | `from diagrams.oci.connectivity import CustomerDatacntrWhite` |
| `from diagrams.oci.connectivity import Customerpremisesequip`      | `from diagrams.oci.connectivity import CustomerPremise`       |
| `from diagrams.oci.connectivity import CustomerpremisesequipWhite` | `from diagrams.oci.connectivity import CustomerPremiseWhite`  |
| `from diagrams.oci.connectivity import Fastconnect`                | `from diagrams.oci.connectivity import FastConnect`           |
| `from diagrams.oci.connectivity import FastconnectWhite`           | `from diagrams.oci.connectivity import FastConnectWhite`      |
| `from diagrams.oci.connectivity import Vpn`                        | `from diagrams.oci.connectivity import VPN`                   |
| `from diagrams.oci.connectivity import VpnWhite`                   | `from diagrams.oci.connectivity import VPNWhite`              |
| `from diagrams.oci.database import AutonomousDatabase`             | `from diagrams.oci.database import Autonomous`                |
| `from diagrams.oci.database import AutonomousDatabaseWhite`        | `from diagrams.oci.database import AutonomousWhite`           |
| `from diagrams.oci.database import Databaseservice`                | `from diagrams.oci.database import DatabaseService`           |
| `from diagrams.oci.database import DatabaseserviceWhite`           | `from diagrams.oci.database import DatabaseServiceWhite`      |
| `from diagrams.oci.devops import Apigateway`                       | `from diagrams.oci.devops import APIGateway`                  |
| `from diagrams.oci.devops import ApigatewayWhite`                  | `from diagrams.oci.devops import APIGatewayWhite`             |
| `from diagrams.oci.devops import Apiservice`                       | `from diagrams.oci.devops import APIService`                  |
| `from diagrams.oci.devops import ApiserviceWhite`                  | `from diagrams.oci.devops import APIServiceWhite`             |
| `from diagrams.oci.devops import Resourcemgmt`                     | `from diagrams.oci.devops import ResourceMgmt`                |
| `from diagrams.oci.devops import ResourcemgmtWhite`                | `from diagrams.oci.devops import ResourceMgmtWhite`           |
| `from diagrams.oci.edge import Cdn`                                | `from diagrams.oci.connectivity import CDN`                   |
| `from diagrams.oci.edge import CdnWhite`                           | `from diagrams.oci.connectivity import CDNWhite`              |
| `from diagrams.oci.edge import Dns`                                | `from diagrams.oci.connectivity import DNS`                   |
| `from diagrams.oci.edge import DnsWhite`                           | `from diagrams.oci.connectivity import DNSWhite`              |
| `from diagrams.oci.edge import Emaildelivery`                      | `from diagrams.oci.monitoring import Email`                   |
| `from diagrams.oci.edge import EmaildeliveryWhite`                 | `from diagrams.oci.monitoring import EmailWhite`              |
| `from diagrams.oci.edge import Waf`                                | `from diagrams.oci.security import WAF`                       |
| `from diagrams.oci.edge import WafWhite`                           | `from diagrams.oci.security import WAFWhite`                  |
| `from diagrams.oci.monitoring import Event`                        | `from diagrams.oci.monitoring import Events`                  |
| `from diagrams.oci.monitoring import EventWhite`                   | `from diagrams.oci.monitoring import EventsWhite`             |
| `from diagrams.oci.monitoring import Healthcheck`                  | `from diagrams.oci.monitoring import HealthCheck`             |
| `from diagrams.oci.monitoring import HealthcheckWhite`             | `from diagrams.oci.monitoring import HealthCheckWhite`        |
| `from diagrams.oci.monitoring import Logging`                      | `from diagrams.oci.governance import Logging`                 |
| `from diagrams.oci.monitoring import LoggingWhite`                 | `from diagrams.oci.governance import LoggingWhite`            |
| `from diagrams.oci.monitoring import Queuing`                      | `from diagrams.oci.monitoring import Queue`                   |
| `from diagrams.oci.monitoring import QueuingWhite`                 | `from diagrams.oci.monitoring import QueueWhite`              |
| `from diagrams.oci.network import Internetgateway`                 | `from diagrams.oci.network import InternetGateway`            |
| `from diagrams.oci.network import InternetgatewayWhite`            | `from diagrams.oci.network import InternetGatewayWhite`       |
| `from diagrams.oci.network import Loadbalance`                     | `from diagrams.oci.network import LoadBalancer`               |
| `from diagrams.oci.network import LoadbalanceWhite`                | `from diagrams.oci.network import LoadBalancerWhite`          |
| `from diagrams.oci.network import NATgateway`                      | `from diagrams.oci.connectivity import NATGateway`            |
| `from diagrams.oci.network import NATgatewayWhite`                 | `from diagrams.oci.connectivity import NATGatewayWhite`       |
| `from diagrams.oci.network import Routetable`                      | `from diagrams.oci.network import RouteTable`                 |
| `from diagrams.oci.network import RoutetableWhite`                 | `from diagrams.oci.network import RouteTableWhite`            |
| `from diagrams.oci.network import Securitylists`                   | `from diagrams.oci.network import SecurityLists`              |
| `from diagrams.oci.network import SecuritylistsWhite`              | `from diagrams.oci.network import SecurityListsWhite`         |
| `from diagrams.oci.network import Vcloudnetwork`                   | `from diagrams.oci.network import Vcn`                        |
| `from diagrams.oci.network import VcloudnetworkWhite`              | `from diagrams.oci.network import VcnWhite`                   |
| `from diagrams.oci.security import Audit`                          | `from diagrams.oci.governance import Audit`                   |
| `from diagrams.oci.security import AuditWhite`                     | `from diagrams.oci.governance import AuditWhite`              |
| `from diagrams.oci.security import Compartments`                   | `from diagrams.oci.governance import Compartments`            |
| `from diagrams.oci.security import CompartmentsWhite`              | `from diagrams.oci.governance import CompartmentsWhite`       |
| `from diagrams.oci.security import Ddos`                           | `from diagrams.oci.security import DDOS`                      |
| `from diagrams.oci.security import DdosWhite`                      | `from diagrams.oci.security import DDOSWhite`                 |
| `from diagrams.oci.security import Groups`                         | `from diagrams.oci.governance import Groups`                  |
| `from diagrams.oci.security import GroupsWhite`                    | `from diagrams.oci.governance import GroupsWhite`             |
| `from diagrams.oci.security import IdAccess`                       | `from diagrams.oci.security import IDAccess`                  |
| `from diagrams.oci.security import IdAccessWhite`                  | `from diagrams.oci.security import IDAccessWhite`             |
| `from diagrams.oci.security import Keymgmt`                        | `from diagrams.oci.security import KeyManagement`             |
| `from diagrams.oci.security import KeymgmtWhite`                   | `from diagrams.oci.security import KeyManagementWhite`        |
| `from diagrams.oci.security import Ocid`                           | `from diagrams.oci.governance import OCID`                    |
| `from diagrams.oci.security import OcidWhite`                      | `from diagrams.oci.governance import OCIDWhite`               |
| `from diagrams.oci.security import Policies`                       | `from diagrams.oci.governance import Policies`                |
| `from diagrams.oci.security import PoliciesWhite`                  | `from diagrams.oci.governance import PoliciesWhite`           |
| `from diagrams.oci.security import Tagging`                        | `from diagrams.oci.governance import Tagging`                 |
| `from diagrams.oci.security import TaggingWhite`                   | `from diagrams.oci.governance import TaggingWhite`            |
| `from diagrams.oci.storage import Backuprestore`                   | `from diagrams.oci.storage import BackupRestore`              |
| `from diagrams.oci.storage import BackuprestoreWhite`              | `from diagrams.oci.storage import BackupRestoreWhite`         |
| `from diagrams.oci.storage import Blockstorage`                    | `from diagrams.oci.storage import BlockStorage`               |
| `from diagrams.oci.storage import BlockstorageWhite`               | `from diagrams.oci.storage import BlockStorageWhite`          |
| `from diagrams.oci.storage import Datatransfer`                    | `from diagrams.oci.storage import DataTransfer`               |
| `from diagrams.oci.storage import DatatransferWhite`               | `from diagrams.oci.storage import DataTransferWhite`          |
| `from diagrams.oci.storage import Filestorage`                     | `from diagrams.oci.storage import FileStorage`                |
| `from diagrams.oci.storage import FilestorageWhite`                | `from diagrams.oci.storage import FileStorageWhite`           |
| `from diagrams.oci.storage import Objectstorage`                   | `from diagrams.oci.storage import ObjectStorage`              |
| `from diagrams.oci.storage import ObjectstorageWhite`              | `from diagrams.oci.storage import ObjectStorageWhite`         |
| `from diagrams.oci.storage import Storagegateway`                  | `from diagrams.oci.storage import StorageGateway`             |
| `from diagrams.oci.storage import StoragegatewayWhite`             | `from diagrams.oci.storage import StorageGatewayWhite`        |

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
