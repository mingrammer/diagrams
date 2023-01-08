# fmt: off

#########################
#      Application      #
#########################

APP_NAME = "diagrams"

DIR_DOC_ROOT = "docs/nodes"
DIR_APP_ROOT = "diagrams"
DIR_RESOURCE = "resources"
DIR_TEMPLATE = "templates"

PROVIDERS = (
    "base",
    "onprem",
    "aws",
    "azure",
    "digitalocean",
    "gcp",
    "ibm",
    "firebase",
    "k8s",
    "alibabacloud",
    "oci",
    "programming",
    "saas",
    "elastic",
    "generic",
    "openstack",
    "outscale",
)

#########################
#  Resource Processing  #
#########################

CMD_ROUND = "round"
CMD_ROUND_OPTS = ("-w",)
CMD_SVG2PNG = "inkscape"
CMD_SVG2PNG_OPTS = ("-w", "256", "-h", "256", "--export-type", "png")
CMD_SVG2PNG_IM = "convert"
CMD_SVG2PNG_IM_OPTS = ("-shave", "25%x25%", "-resize", "256x256!")

FILE_PREFIXES = {
    "onprem": (),
    "aws": ("Amazon-", "AWS-"),
    "azure": ("Azure-",),
    "digitalocean": (),
    "gcp": ("Cloud-",),
    "firebase": ("Cloud-",),
    "ibm": (),
    "k8s": (),
    "alibabacloud": (),
    "oci": ("OCI-icon-",),
    "programming": (),
    "saas": (),
    "elastic": (),
    "outscale": (),
    "generic": (),
    "openstack": (),
}

#########################
#  Doc Auto Generation  #
#########################

TMPL_APIDOC = "apidoc.tmpl"

#########################
# Class Auto Generation #
#########################

TMPL_MODULE = "module.tmpl"

UPPER_WORDS = {
    "aws": ("aws", "api", "ebs", "ec2", "efs", "emr", "rds", "ml", "mq", "nat", "vpc", "waf", "sdk"),
    "azure": ("ad", "b2c", "ai", "api", "cdn", "ddos", "dns", "fxt", "hana", "hd", "id", "sap", "sql", "vm", "vpn", "vpc"),
    "gcp": ("gcp", "ai", "api", "cdn", "dns", "gke", "gpu", "iap", "ml", "nat", "os", "sdk", "sql", "tpu", "vpn"),
    "firebase": ("ab", "fcm", "ml"),
    "k8s": (
        "api", "cm", "ccm", "crb", "crd", "ds", "etcd", "hpa", "k8s", "ns", "psp", "pv", "pvc", "rb", "rs",
        "sa", "sc", "sts", "svc",
    ),
    "oci": ("oci", "ocid", "oke", "ocir", "ddos", "waf", "bm", "vm", "cdn", "vpn", "dns", "nat", "dms", "api", "id"),
    "elastic": ("apm", "siem", "ece", "eck", "sql"),
    "generic": ("vpn", "ios", "xen", "sql", "lxc"),
    "outscale": ("osc",),
    "openstack": ("rpm", "loci", "nfv", "ec2api"),
    "pve": ("pve"),
    "ibm": ("ibm"),
}

TITLE_WORDS = {
    "onprem": {
        "onprem": "OnPrem",
    },
    "alibabacloud": {
        "alibabacloud": "AlibabaCloud"
    },
    "aws": {
        "cloudfront": "CloudFront"
    },
    "digitalocean": {
        "digitalocean": "DigitalOcean"
    },
    "openstack": {
        "openstack": "OpenStack"
    },
    "ibm": {
        "ibm": "IBMCloud"
    },
}

# TODO: check if the classname exists
ALIASES = {
    "onprem": {
        "analytics": {
            "Powerbi": "PowerBI"
        },
        "ci": {
            "Circleci": "CircleCI",
            "Concourseci": "ConcourseCI",
            "Droneci": "DroneCI",
            "Gitlabci": "GitlabCI",
            "Travisci": "TravisCI",
            "Teamcity": "TC",
            "Zuulci": "ZuulCI",
        },
        "container": {
            "Lxc": "LXC",
            "Rkt": "RKT",
        },
        "database": {
            "Clickhouse": "ClickHouse",
            "Cockroachdb": "CockroachDB",
            "Couchdb": "CouchDB",
            "Hbase": "HBase",
            "Influxdb": "InfluxDB",
            "Janusgraph": "JanusGraph",
            "Mariadb": "MariaDB",
            "Mongodb": "MongoDB",
            "Mssql": "MSSQL",
            "Mysql": "MySQL",
            "Postgresql": "PostgreSQL",
        },
        "gitops": {
            "Argocd": "ArgoCD",
        },
        "logging": {
            "Fluentbit": "FluentBit",
            "Rsyslog": "RSyslog",
        },
        "network": {
            "Etcd": "ETCD",
            "Haproxy": "HAProxy",
            "OpenServiceMesh": "OSM",
            "Opnsense": "OPNSense",
            "Pfsense": "PFSense",
            "Vyos": "VyOS"
        },
        "proxmox": {
            "Pve": "ProxmoxVE",
        },
        "queue": {
            "Activemq": "ActiveMQ",
            "Emqx": "EMQX",
            "Rabbitmq": "RabbitMQ",
            "Zeromq": "ZeroMQ",
        },
        "storage": {
            "Ceph": "CEPH",
            "CephOsd": "CEPH_OSD",
        },
        "workflow": {
            "Kubeflow": "KubeFlow",
            "Nifi": "NiFi",
        }
    },
    "aws": {
        "analytics": {
            "ElasticsearchService": "ES",
        },
        "business": {
            "AlexaForBusiness": "A4B"
        },
        "blockchain": {
            "QuantumLedgerDatabaseQldb": "QLDB"
        },
        "compute": {
            "ApplicationAutoScaling": "AutoScaling",
            "EC2Ami": "AMI",
            "EC2ContainerRegistry": "ECR",
            "ElasticBeanstalk": "EB",
            "ElasticContainerService": "ECS",
            "ElasticKubernetesService": "EKS",
            "ServerlessApplicationRepository": "SAR",
        },
        "database": {
            "DatabaseMigrationService": "DMS",
            "DocumentdbMongodbCompatibility": "DocumentDB",
            "DynamodbDax": "DAX",
            "DynamodbGlobalSecondaryIndex": "DynamodbGSI",
            "Database": "DB",
            "Dynamodb": "DDB",
            "Elasticache": "ElastiCache",
            "QuantumLedgerDatabaseQldb": "QLDB",
        },
        "devtools": {
            "CommandLineInterface": "CLI",
            "DeveloperTools": "DevTools",
        },
        "engagement": {
            "SimpleEmailServiceSes": "SES",
        },
        "general": {
            "GenericOfficeBuilding": "OfficeBuilding",
        },
        "integration": {
            "SimpleNotificationServiceSns": "SNS",
            "SimpleQueueServiceSqs": "SQS",
            "StepFunctions": "SF",
        },
        "iot": {
            "Freertos": "FreeRTOS",
            "IotHardwareBoard": "IotBoard",
        },
        "management": {
            "SystemsManager": "SSM",
            "SystemsManagerParameterStore": "ParameterStore",
        },
        "migration": {
            "ApplicationDiscoveryService": "ADS",
            "CloudendureMigration": "CEM",
            "DatabaseMigrationService": "DMS",
            "MigrationAndTransfer": "MAT",
            "ServerMigrationService": "SMS",
        },
        "ml": {
            "DeepLearningContainers": "DLC",
        },
        "network": {
            "CloudFront": "CF",
            "ElasticLoadBalancing": "ELB",
            "ElbApplicationLoadBalancer": "ALB",
            "ElbClassicLoadBalancer": "CLB",
            "ElbNetworkLoadBalancer": "NLB",
            "GlobalAccelerator": "GAX",
        },
        "security": {
            "CertificateManager": "ACM",
            "Cloudhsm": "CloudHSM",
            "DirectoryService": "DS",
            "FirewallManager": "FMS",
            "IdentityAndAccessManagementIamAccessAnalyzer": "IAMAccessAnalyzer",
            "IdentityAndAccessManagementIamAWSSts": "IAMAWSSts",
            "IdentityAndAccessManagementIamPermissions": "IAMPermissions",
            "IdentityAndAccessManagementIamRole": "IAMRole",
            "IdentityAndAccessManagementIam": "IAM",
            "KeyManagementService": "KMS",
            "ResourceAccessManager": "RAM",
        },
        "storage": {
            "CloudendureDisasterRecovery": "CDR",
            "ElasticBlockStoreEBS": "EBS",
            "ElasticFileSystemEFS": "EFS",
            "Fsx": "FSx",
            "SimpleStorageServiceS3": "S3",
        },
    },
    "azure": {
        "compute": {
            "ContainerRegistries": "ACR",
            "KubernetesServices": "AKS",
            "VMScaleSet": "VMSS"
        },
    },
    "gcp": {
        "analytics": {
            "Bigquery": "BigQuery",
            "Pubsub": "PubSub",
        },
        "compute": {
            "AppEngine": "GAE",
            "Functions": "GCF",
            "ComputeEngine": "GCE",
            "KubernetesEngine": "GKE",
        },
        "database": {
            "Bigtable": "BigTable",
        },
        "devtools": {
            "ContainerRegistry": "GCR",
        },
        "ml": {
            "Automl": "AutoML",
            "NaturalLanguageAPI": "NLAPI",
            "SpeechToText": "STT",
            "TextToSpeech": "TTS",
        },
        "network": {
            "VirtualPrivateCloud": "VPC"
        },
        "security": {
            "KeyManagementService": "KMS",
            "SecurityCommandCenter": "SCC",
        },
        "storage": {
            "Storage": "GCS",
        },
    },
    "firebase": {
        "grow": {
            "Messaging": "FCM"
        }
    },
    "k8s": {
        "clusterconfig": {
            "Limits": "LimitRange",
            "HPA": "HorizontalPodAutoscaler",
        },
        "compute": {
            "Deploy": "Deployment",
            "DS": "DaemonSet",
            "RS": "ReplicaSet",
            "STS": "StatefulSet"
        },
        "controlplane": {
            "API": "APIServer",
            "CM": "ControllerManager",
            "KProxy": "KubeProxy",
            "Sched": "Scheduler",
        },
        "group": {
            "NS": "Namespace",
        },
        "network": {
            "Ep": "Endpoint",
            "Ing": "Ingress",
            "Netpol": "NetworkPolicy",
            "SVC": "Service",
        },
        "podconfig": {
            "CM": "ConfigMap",
        },
        "rbac": {
            "CRole": "ClusterRole",
            "CRB": "ClusterRoleBinding",
            "RB": "RoleBinding",
            "SA": "ServiceAccount",
        },
        "storage": {
            "PV": "PersistentVolume",
            "PVC": "PersistentVolumeClaim",
            "SC": "StorageClass",
            "Vol": "Volume",
        },
    },
    "alibabacloud": {
        "application": {
            "LogService": "SLS",
            "MessageNotificationService": "MNS",
            "PerformanceTestingService": "PTS",
            "SmartConversationAnalysis": "SCA",
        },
        "compute": {
            "AutoScaling": "ESS",
            "ElasticComputeService": "ECS",
            "ElasticContainerInstance": "ECI",
            "ElasticHighPerformanceComputing": "EHPC",
            "FunctionCompute": "FC",
            "OperationOrchestrationService": "OOS",
            "ResourceOrchestrationService": "ROS",
            "ServerLoadBalancer": "SLB",
            "ServerlessAppEngine": "SAE",
            "SimpleApplicationServer": "SAS",
            "WebAppService": "WAS",
        },
        "database": {
            "DataManagementService": "DMS",
            "DataTransmissionService": "DTS",
            "DatabaseBackupService": "DBS",
            "DisributeRelationalDatabaseService": "DRDS",
            "GraphDatabaseService": "GDS",
            "RelationalDatabaseService": "RDS",
        },
        "network": {
            "CloudEnterpriseNetwork": "CEN",
            "ElasticIpAddress": "EIP",
            "ServerLoadBalancer": "SLB",
            "VirtualPrivateCloud": "VPC",
        },
        "security": {
            "AntiBotService": "ABS",
            "AntifraudService": "AS",
            "CloudFirewall": "CFW",
            "ContentModeration": "CM",
            "DataEncryptionService": "DES",
            "WebApplicationFirewall": "WAF",
        },
        "storage": {
            "FileStorageHdfs": "HDFS",
            "FileStorageNas": "NAS",
            "HybridBackupRecovery": "HBR",
            "HybridCloudDisasterRecovery": "HDR",
            "ObjectStorageService": "OSS",
            "ObjectTableStore": "OTS",
        }
    },
    "digitalocean": {},
    "oci": {
        "compute": {
            "VM": "VirtualMachine",
            "VMWhite": "VirtualMachineWhite",
            "BM": "BareMetal",
            "BMWhite": "BareMetalWhite",
            "OCIR": "OCIRegistry",
            "OCIRWhite": "OCIRegistryWhite",
            "OKE": "ContainerEngine",
            "OKEWhite": "ContainerEngineWhite",
        },
        "database": {
            "Autonomous": "ADB",
            "AutonomousWhite": "ADBWhite",
            "DatabaseService": "DBService",
            "DatabaseServiceWhite": "DBServiceWhite",
        }
    },
    "programming": {
        "framework": {
            "Fastapi": "FastAPI",
            "Graphql": "GraphQL"
        },
        "language": {
            "Javascript": "JavaScript",
            "Nodejs": "NodeJS",
            "Php": "PHP",
            "Typescript": "TypeScript"
        },
    },
    "saas": {
        "logging": {
            "Datadog": "DataDog",
            "Newrelic": "NewRelic"
        }
    },
    "elastic": {
        "elasticsearch": {
            "Elasticsearch": "ElasticSearch",
            "Logstash": "LogStash",
            "MachineLearning": "ML",
        }
    },
    "outscale": {
        "Osc": "OSC",
    },
    "ibm": {},
    "generic": {},
    "openstack": {
        "user": {
            "Openstackclient": "OpenStackClient",
        },
        "billing": {
            "Cloudkitty": "CloudKitty",
        },
        "deployment": {
            "Kolla": "KollaAnsible",
            "Tripleo": "TripleO",
        }
    },
}
