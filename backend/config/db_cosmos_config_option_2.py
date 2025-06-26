# db_config.py

from azure.cosmos import CosmosClient, PartitionKey
from langchain_openai import AzureOpenAIEmbeddings
import os

# Configuración de Azure Cosmos DB
HOST = os.getenv('COSMOSDB_ENDPOINT')
KEY = os.getenv('COSMOSDB_KEY')
cosmos_client = CosmosClient(HOST, KEY)
database_name = os.getenv('COSMOSDB_DATABASE_OPTION_2')
container_name = os.getenv('COSMOSDB_CONTAINER_VECTOR_OPTION_2')
partition_key = PartitionKey(path="/id")
db_config_option_2 = {
    'cosmos_client': cosmos_client,
    'vector_embedding_policy': {
        "vectorEmbeddings": [
            {
                "path": "/embedding",
                "dataType": "float32",
                "distanceFunction": "cosine",
                "dimensions": 1536,
            }
        ]
    },
    'indexing_policy': {
        "indexingMode": "consistent",
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}],
    },
    'cosmos_container_properties': {"partition_key": partition_key},
    'cosmos_database_properties': {},
    'database_name': database_name,
    'container_name': container_name,
    'create_container': False
}