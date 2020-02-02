# fmt: off

#########################
#      Application      #
#########################

APP_NAME = "diagrams"

DIR_APP_ROOT = "diagrams"
DIR_RESOURCE = "resources"
DIR_TEMPLATE = "templates"

PROVIDERS = ("base", "aws", "azure", "gcp")

#########################
#  Resource Processing  #
#########################

CMD_ROUND = "round"
CMD_ROUND_OPTS = ("-w",)
CMD_SVG2PNG = "inkscape"
CMD_SVG2PNG_OPTS = ("-z", "-w", "256", "-h", "256", "--export-type", "png")

FILE_PREFIXES = {
    "aws": ("amazon-", "aws-"),
    "azure": ("azure-",),
    "gcp": ("cloud-",)
}

#########################
# Class Auto Generation #
#########################

TMPL_MODULE = "module.tmpl"

UPPER_WORDS = {
    "aws": ("aws", "api", "ebs", "ec2", "efs", "emr", "rds", "ml", "mq", "vpc", "waf"),
    "azure": ("ad", "b2c", "ai", "api", "cdn", "ddos", "dns", "fxt", "hana", "hd", "id", "sap", "sql", "vm"),
    "gcp": ("gcp", "ai", "api", "cdn", "dns", "gke", "gpu", "ml", "nat", "os", "sdk", "sql", "tpu", "vpn"),
}

# TODO: check if the classname exists
ALIASES = {
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
            "Database": "DB",
            "Dynamodb": "DDB",
            "Elasticache": "ElastiCache",
            "QuantumLedgerDatabaseQldb": "QLDB",
        },
        "devtools": {
            "CommandLineInterface": "CLI",
            "DeveloperTools": "DevTools",
        },
        "integration": {
            "SimpleNotificationServiceSns": "SNS",
            "SimpleQueueServiceSqs": "SQS",
            "StepFunctions": "SF",
        },
        "iot": {
            "Freertos": "FreeRTOS",
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
            "Cloudfront": "CF",
            "ElasticLoadBalancing": "ELB",
            "GlobalAccelerator": "GAX",
        },
        "security": {
            "CertificateManager": "ACM",
            "Cloudhsm": "CloudHSM",
            "DirectoryService": "DS",
            "FirewallManager": "FMS",
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
}
