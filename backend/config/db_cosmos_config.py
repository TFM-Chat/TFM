# db_config.py

from azure.cosmos import CosmosClient, PartitionKey #Importa las clases principales del SDK de Azure Cosmos DB para crear el cliente y definir claves de partición
from langchain_openai import AzureOpenAIEmbeddings #Importa la clase para generar embeddings usando Azure OpenAI
import os #Importa el módulo para acceder a variables de entorno

# Configuración de Azure Cosmos DB
HOST = os.getenv('COSMOSDB_ENDPOINT') #Obtiene el endpoint de Cosmos DB desde variables de entorno
KEY = os.getenv('COSMOSDB_KEY') #Obtiene la clave de acceso de Cosmos DB desde variables de entorno
cosmos_client = CosmosClient(HOST, KEY) #Crea el cliente de Cosmos DB usando el endpoint y la clave
database_name = os.getenv('COSMOSDB_DATABASE') #Obtiene el nombre de la base de datos desde variables de entorno
container_name = os.getenv('COSMOSDB_CONTAINER_VECTOR') #Obtiene el nombre del contenedor para vectores desde variables de entorno
partition_key = PartitionKey(path="/id") #Define la clave de partición usando el campo "id"
db_config = {
    'cosmos_client': cosmos_client, #Referencia al cliente de Cosmos DB
    'vector_embedding_policy': {  #Define la política de embeddings vectoriales
        "vectorEmbeddings": [ #Configuración específica de embeddings 
            {
                "path": "/embedding",
                "dataType": "float32",
                "distanceFunction": "cosine",  #función de distancia
                "dimensions": 1536,
                
            }
        ]
    },
    'indexing_policy': { #Define cómo se indexan los documentos
        "indexingMode": "consistent", #Modo de indexación consistente
        "includedPaths": [{"path": "/*"}], #Especifica qué rutas incluir del índice
        "excludedPaths": [{"path": '/"_etag"/?'}], #Especifica qué rutas excluir del índice
        "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}], #Configuración de índices vectoriales para embeddings con tipo "quantizedFlat"
    },
    'cosmos_container_properties': {"partition_key": partition_key}, #Propiedades específicas del contenedor incluyendo la clave de partición
    'cosmos_database_properties': {}, #Propiedades de la base de datos (vacías en este caso)
    'database_name': database_name, 
    'container_name': container_name,
    'create_container': False  #Indica que no se debe crear automáticamente el contenedor
}