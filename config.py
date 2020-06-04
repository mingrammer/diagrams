# fmt: off

#########################
#      Application      #
#########################

APP_NAME = "diagrams"

DIR_DOC_ROOT = "docs/nodes"
DIR_APP_ROOT = "diagrams"
DIR_RESOURCE = "resources"
DIR_TEMPLATE = "templates"

PROVIDERS = ("base", "onprem", "aws", "azure", "gcp", "firebase", "k8s", "alibabacloud", "oci", "programming", "saas", "elastic", "generic")

#########################
#  Resource Processing  #
#########################

CMD_ROUND = "round"
CMD_ROUND_OPTS = ("-w",)
CMD_SVG2PNG = "inkscape"
CMD_SVG2PNG_OPTS = ("-z", "-w", "256", "-h", "256", "--export-type", "png")
CMD_SVG2PNG_IM = "convert"
CMD_SVG2PNG_IM_OPTS = ("-shave", "25%x25%", "-resize", "256x256!")

FILE_PREFIXES = {
    "onprem": (),
    "aws": ("Amazon-", "AWS-"),
    "azure": ("Azure-",),
    "gcp": ("Cloud-",),
    "firebase": ("Cloud-",),
    "k8s": (),
    "alibabacloud": (),
    "oci": ("OCI-",),
    "programming": (),
    "saas": (),
    "elastic": (),
    "generic": (),
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
    "azure": ("ad", "b2c", "ai", "api", "cdn", "ddos", "dns", "fxt", "hana", "hd", "id", "sap", "sql", "vm"),
    "gcp": ("gcp", "ai", "api", "cdn", "dns", "gke", "gpu", "iap", "ml", "nat", "os", "sdk", "sql", "tpu", "vpn"),
    "firebase": ("ab", "fcm", "ml"),
    "k8s": (
        "api", "cm", "ccm", "crb", "crd", "ds", "etcd", "hpa", "k8s", "ns", "psp", "pv", "pvc", "rb", "rs",
        "sa", "sc", "sts", "svc",
    ),
    "oci": ("oci",),
    "elastic": ("apm", "siem", "ece", "eck"),
    "generic": ("vpn",),
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
    }
}

# TODO: check if the classname exists
ALIASES = {
    "onprem": {
        "ci": {
            "Circleci": "CircleCI",
            "Gitlabci": "GitlabCI",
            "Travisci": "TravisCI",
            "Teamcity": "TC",
            "Zuulci": "ZuulCI",
        },
        "container": {
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
            "Logstash": "LogStash",
        },
        "network": {
            "Etcd": "ETCD",
            "Haproxy": "HAProxy",
            "Pfsense": "PFSense",
            "Vyos": "VyOS"
        },
        "queue": {
            "Activemq": "ActiveMQ",
            "Rabbitmq": "RabbitMQ",
            "Zeromq": "ZeroMQ",
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
        "compute": {
            "ApplicationAutoScaling": "AutoScaling",
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
            "PV": "PersistnetVolume",
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
    "oci": {
        "compute": {
            "Vm": "VirtualMachine",
            "VmGrey": "VirtualMachineGrey",
            "Bm": "BareMetal",
            "BmGrey": "BareMetalGrey",
        },
        "database": {
            "Databaseservice": "DBService",
            "DatabaseserviceGrey": "DBServiceGrey",
        }
    },
    "programming": {
        "language": {
            "Javascript": "JavaScript",
            "Nodejs": "NodeJS",
            "Php": "PHP",
            "Typescript": "TypeScript"
        },
    },
    "saas": {},
    "elastic": {
        "elasticsearch": {
            "Logstash": "LogStash",
        }
    },
    "generic": {},
}
