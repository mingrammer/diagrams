# Changelogs

## 0.16.0

### Breaking Changes

- The following import changes:
  - from diagrams.onprem.logging import Logstash is now from diagrams.elastic.elasticsearch import Logstash
  - from diagrams.onprem.monitoring import Kibana is now from diagrams.elastic.elasticsearch import Kibana
  - from diagrams.onprem.search import Elasticsearch(*) is now from diagrams.elastic.elasticsearch import Elasticsearch
  *The previous icon was the company icon not the elasticsearch product, for the company icon: from diagrams.elastic.saas import Elastic

### Added

- Add more logging
- Updated OCI icon set (2020)
- add cloudinary logo in media management category
- Docker local development setup
- Add Openstack as cloud provider

### Fixed

- fix: typo in comment

## 0.15.0

### Added

- feat(option): add curvestyle option (ortho or curved)
- New Auth0, Cloudflare, Recombee Nodes
- check for black linter in autogen.sh
- Update readme
- docs(readme): update who use it
- docs(readme): add Cloudiscovery in "who use it" list

### Fixed

- fix(edge): misaligned label text position
- Fix typo for PersistentVolume
