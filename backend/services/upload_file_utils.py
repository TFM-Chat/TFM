from azure.storage.blob import BlobServiceClient
import os
import logging
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain.text_splitter import CharacterTextSplitter
from config.db_cosmos_config import db_config
from services.model_service import get_embeddings
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos import CosmosClient
from vectorstores.factory import get_vectorstore_class
import logging
import requests
import os


# Configuración de Cosmos DB desde el archivo .env
url = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")

# Conexión al cliente de Cosmos DB
client = CosmosClient(url, credential=key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)


def upload_to_blob_storage(file, file_name):
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
        container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME')
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        # Subir el archivo
        blob_client.upload_blob(file)

        # Obtener la URL del blob
        url = f'{blob_client.primary_endpoint}'
        return url

def get_file_size(file_url):
    try:
        response = requests.head(file_url, allow_redirects=True)
        file_size = int(response.headers.get('content-length', 0))
        return file_size if file_size > 0 else None
    except Exception as e:
        logging.error(f"Error al calcular el tamaño del archivo desde la URL: {str(e)}")
        return None
    

def extract_text_from_document(file_path):
    try:
        logging.info(f'Extrayendo texto desde: {file_path}')
        endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
        api_model_id = os.getenv("DOCUMENT_INTELLIGENCE_MODEL")

        loader = AzureAIDocumentIntelligenceLoader(
            api_endpoint=endpoint, 
            api_key=key, 
            url_path=file_path, 
            api_model=api_model_id
        )

        documents = loader.load()
        return documents  # List of Document objects
    except Exception as e:
        logging.error(f"Error al extraer texto del documento: {str(e)}")
        return None

def chunk_document(documents, chunk_size, chunk_overlap):
    try:
        logging.info(f'Iniciando el chunking del documento')
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator='\n'
        )
        chunks = text_splitter.split_documents(documents)
        logging.info(f'Chunking completado. Total de fragmentos: {len(chunks)}')
        return chunks
    except Exception as e:
        logging.error(f"Error durante el chunking del documento: {str(e)}")
        return None
    
def vectorize_and_save_to_cosmos(chunks, metadata):
    try:
        # Obtener los embeddings
        embeddings = get_embeddings()

        # Vectorizar y almacenar en Cosmos DB
        vectorstore_class = get_vectorstore_class("CosmosDB")
        # Asignar metadatos adicionales a cada fragmento
        for idx, doc in enumerate(chunks):
            doc.metadata=metadata
            doc.metadata["chunk_index"] = idx + 1  # Índice del chunk
        vectorstore_class.from_documents(chunks, embeddings,db_config)
        #vectorstore = store_class.from_documents(all_docs, emebedding_selected, db_config_vectorize)
       
        logging.info(f'Metadatos y vectorización guardados correctamente en Cosmos DB.')
    except Exception as e:
        logging.error(f"Error durante la vectorización o almacenamiento en Cosmos DB: {str(e)}")

# Función para eliminar el archivo de Blob Storage
def rollback_blob(file_name):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
        container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME')
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.delete_blob()
        logging.info(f"Archivo {file_name} eliminado de Blob Storage durante el rollback.")
    except Exception as e:
        logging.error(f"Error al eliminar el archivo del Blob Storage: {str(e)}")

# Función para eliminar entradas de Cosmos DB basadas en la URL
def rollback_cosmos(url_to_delete):
    query = f"SELECT * FROM c WHERE c.url = '{url_to_delete}'"
    
    try:
        # Borrar cada documento que coincida con la URL
        for item in container.query_items(query=query, enable_cross_partition_query=True):
            try:
                # Aquí utilizamos 'id' como la clave de partición para la eliminación
                container.delete_item(item['id'], partition_key=item['id'])
                logging.info(f"Eliminado el documento con id: {item['id']} y partitionKey: {item['id']}")
            except exceptions.CosmosResourceNotFoundError:
                logging.warning(f"Documento con id: {item['id']} no encontrado o ya eliminado.")
            except Exception as e:
                logging.error(f"Ocurrió un error al intentar eliminar el documento con id: {item['id']}. Error: {e}")
        
        logging.info("Todos los registros posibles han sido procesados para eliminación.")
    
    except Exception as e:
        logging.error(f"Error al consultar o eliminar las entradas de Cosmos DB: {str(e)}")

# Función para revertir cambios en el índice de Azure Cognitive Search
def rollback_index_update():
    try:
        # Implementa la lógica para revertir cambios en el índice de Azure Search
        logging.info("Rollback del índice de Azure Search realizado.")
    except Exception as e:
        logging.error(f"Error durante el rollback del índice de Azure Search: {str(e)}")

