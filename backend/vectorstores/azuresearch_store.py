import logging #Importa el módulo de logging para registrar eventos y errores
from langchain_community.vectorstores.azuresearch import AzureSearch #Importa la clase de LangChain para vectorstore de Cosmos DB NoSQL
from logging_module.logging_config import setup_logging #Configuración personalizada de logging adaptada a los requerimientos del proyecto
from vectorstores.base_store import BaseVectorStore #define la interfaz común para todos los tipos de vectorstores implementados
from langchain_community.vectorstores.azure_cosmos_db_no_sql import AzureCosmosDBNoSqlVectorSearch #Proporciona vectorstore para Cosmoscon capacidades de búsqueda vectorial
import json
import os
from azure.cosmos import CosmosClient #Cliente oficial de Azure para conectar y operar con bases de datos Cosmos DB



# Configurar logging
setup_logging()

class AzureSearchStore(BaseVectorStore):
    def __init__(self, vectorstore=None):
        self.vectorstore = vectorstore

    @classmethod
    def load_index(cls,index_path, embeddings, db_config):
        logging.info("Intentando cargar índice desde Azure Search DB NoSQL")
        try:
            if 'cosmos_database_properties' not in db_config:
                raise ValueError("cosmos_database_properties es obligatorio en db_config")
            
            index_name: str = os.getenv("AZURE_SEARCH_INDEX")
            vectorstore: AzureSearch = AzureSearch(
                    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
                    index_name=index_name,
                    embedding_function=embeddings.embed_query,
                    semantic_configuration_name='default',
                    search_type='similarity'
            )
            logging.info("Índice cargado exitosamente desde Azure Cosmos DB NoSQL")
        except KeyError as e:
            logging.error(f"Error: Falta la clave '{e}' en db_config. No se puede cargar el índice.")
            raise
        except Exception as e:
            logging.error(f"Error inesperado al cargar el índice: {e}")
            raise
        
        return cls(vectorstore)

    @classmethod
    def from_documents(cls, documents, embeddings, db_config):
        #TODO:Para consulta no se necesita vectorizar
        
        return ''

    def save_index(self, index_options=None):
        logging.info("Guardando índice en Azure Cosmos DB NoSQL")
        try:
            # No se necesita llamar a `create_index`, ya que el índice es manejado automáticamente por Cosmos DB
            logging.info("No es necesario guardar")
        except Exception as e:
            logging.error(f"Error inesperado al guardar el índice: {e}")
            raise

    def similarity_search_with_score(self, query, k=4 ):
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def as_retriever(self):
        logging.info(f"obteniendo retrieve de Azure Search DB")
        return self.vectorstore.as_retriever()    
    
# Configurar conexión a Cosmos DB
url = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")

client = CosmosClient(url, credential=key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

def query_cosmosdb_for_metadata(doc_ids):
    metadata = {}
    query = f"SELECT c.id, c.url, c.row_number FROM c WHERE c.id IN ({','.join(['"' + str(doc_id) + '"' for doc_id in doc_ids])})"

    try:
        items = container.query_items(query=query, enable_cross_partition_query=True)
        for item in items:
            metadata[item['id']] = {
                'url': item.get('url', 'Desconocido'),
                'row_number': item.get('row_number', 'Desconocido')
            }
    except Exception as e:
        logging.error(f"Error al consultar metadata adicional en Cosmos DB: {e}")

    return metadata