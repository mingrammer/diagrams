from diagrams import Diagram
from diagrams.azure.ml import AzureOpenAI
from diagrams.azure.ml import CognitiveServices
from diagrams.azure.integration import LogicApps
from diagrams.azure.database import CosmosDb
from diagrams.azure.compute import FunctionApps
from diagrams.azure.web import AppServices
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.analytics import EventHubs

with Diagram("Doc IQ Architecture", show=False):
    #AzureOpenAI("Azure OpenAI") >> CognitiveServices("AI Search") >> LogicApps("Document Intelligence") >> CosmosDb("Cosmos DB")

    app_service = AppServices("App Service")
    function_app = FunctionApps("Function App")
    storage_account = StorageAccounts("Storage Account")

    app_service >> function_app >> app_service >> storage_account

    function_app_read_storage = FunctionApps("Read Storage")
    function_app_create_chunks = FunctionApps("Create Chunks")

    storage_account >> function_app_read_storage >> CognitiveServices("DocIntel - OCR") >> function_app_create_chunks >> AzureOpenAI("OpenAI - Embeddings") >> function_app_create_chunks >> CognitiveServices("AI Search")

    event_hub = EventHubs("Event Hub")
    abstract_function_app = FunctionApps("Abstraction")

    function_app_create_chunks >> event_hub >> abstract_function_app >> AzureOpenAI("Chat API") >> abstract_function_app >> CosmosDb("Cosmos DB")