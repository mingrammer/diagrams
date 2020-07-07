# Changelogs

## 0.16.0

### Breaking Changes

- The following import changes:
  - from diagrams.onprem.logging import Logstash is now from diagrams.elastic.elasticsearch import Logstash
  - from diagrams.onprem.monitoring import Kibana is now from diagrams.elastic.elasticsearch import Kibana
  - from diagrams.onprem.search import Elasticsearch(*) is now from diagrams.elastic.elasticsearch import Elasticsearch
  *The previous icon was the company icon not the elasticsearch product, for the company icon: from diagrams.elastic.saas import Elastic

### Added

- Docker local development setup [#210] https://github.com/mingrammer/diagrams/pull/210
- Support OpenStack [#211] https://github.com/mingrammer/diagrams/pull/211

### Fixed

-

## 0.15.0

### Added

- Support curvestyle option (ortho or curved)
- Support Auth0, Cloudflare and Recombee: [#209] https://github.com/mingrammer/diagrams/pull/209


### Fixed

- Fix typo for PersistentVolume: [#207] https://github.com/mingrammer/diagrams/pull/207
- Fix misaligned label text position
