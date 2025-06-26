import logging #Importa el módulo de logging para registrar eventos y errores
from langchain_community.vectorstores.azure_cosmos_db_no_sql import AzureCosmosDBNoSqlVectorSearch #Importa la clase de LangChain para vectorstore de Cosmos DB NoSQL
from logging_module.logging_config import setup_logging #Importa la configuración personalizada de logging
from vectorstores.base_store import BaseVectorStore #Importa la clase base para vectorstores
from datetime import datetime #Importa funciones para manejo de fechas y tiempo
import pytz #Importa biblioteca para manejo de zonas horarias

# Obtener la zona horaria de Colombia
colombia_tz = pytz.timezone('America/Bogota')

import json
import os
from azure.cosmos import CosmosClient, exceptions



# Configurar logging
setup_logging()

class CosmosDBNoSQLStore(BaseVectorStore):
    def __init__(self, vectorstore=None):
        self.vectorstore = vectorstore

    @classmethod
    def load_index(cls,index_path, embeddings, db_config): #Método estático para cargar índice con parámetros de ruta, embeddings y configuración
        logging.info("Intentando cargar índice desde Azure Cosmos DB NoSQL") #Registra el intento de carga del índice
        try:
            if 'cosmos_database_properties' not in db_config: #Verifica si existe la propiedad de base de datos en la configuración
                raise ValueError("cosmos_database_properties es obligatorio en db_config") #Lanza error si falta la configuración requerid
            
            vectorstore = AzureCosmosDBNoSqlVectorSearch(
                cosmos_client=db_config['cosmos_client'], #Asigna el cliente de Cosmos DB desde la configuración
                embedding=embeddings, #Configura el modelo de embeddings para vectorización
                vector_embedding_policy=db_config['vector_embedding_policy'], #Establece la política de embeddings vectoriales
                indexing_policy=db_config['indexing_policy'], #Define la política de indexación para optimizar búsquedas
                cosmos_container_properties=db_config['cosmos_container_properties'], #Configura las propiedades del contenedor
                cosmos_database_properties=db_config['cosmos_database_properties'], #Establece las propiedades de la base de datos
                database_name=db_config.get('database_name', 'vectorSearchDB'), #Obtiene el nombre de la base de datos o usa valor por defecto
                container_name=db_config.get('container_name', 'vectorSearchContainer'), #Obtiene el nombre del contenedor o usa valor por defecto
                create_container=db_config.get('create_container', True) #Define si se debe crear el contenedor automáticamente
            )
            logging.info("Índice cargado exitosamente desde Azure Cosmos DB NoSQL") #Registra el éxito en la carga del índice
        except KeyError as e: #Captura errores de claves faltantes en la configuración
            logging.error(f"Error: Falta la clave '{e}' en db_config. No se puede cargar el índice.") #Registra error específico de clave faltante
            raise #Re-lanza la excepción para manejo superior
        except Exception as e: #Captura cualquier otra excepción no prevista
            logging.error(f"Error inesperado al cargar el índice: {e}") #Registra error inesperado con detalles
            raise
        
        return cls(vectorstore) #Retorna una instancia de la clase con el vectorstore configurado

    @classmethod
    def from_documents(cls, documents, embeddings, db_config): #Define el método que recibe documentos, embeddings y configuración de BD
        logging.info(f"Comenzando la vectorización de {len(documents)} documentos con Azure Cosmos DB NoSQL") #Registra el inicio del proceso
        try:
            if 'cosmos_database_properties' not in db_config: #Valida que exista la propiedad requerida
                raise ValueError("cosmos_database_properties es obligatorio en db_config") #Lanza error si falta configuración
            
            # Registro para verificar la estructura de los documentos
            logging.debug(f"Estructura del primer documento: {documents[0] if documents else 'Ningún documento disponible'}") #Debug del primer documento

            # Acceso a los atributos de `Document`
            texts = [doc.page_content for doc in documents] #Extrae el contenido textual de cada documento
            metadatas = [doc.metadata for doc in documents] #Extrae los metadatos de cada documento
            
            logging.debug(f"Textos extraídos: {texts[:100]}")  #Muestra los primeros 100 caracteres de textos
            logging.debug(f"Metadatos extraídos: {metadatas[:100]}") #Muestra los primeros 100 metadatos

            vectorstore = AzureCosmosDBNoSqlVectorSearch.from_texts( #Crea vectorstore desde textos
                texts=texts,
                embedding=embeddings, #Configura el modelo de embeddings
                metadatas=metadatas, #Asigna los metadatos
                cosmos_client=db_config['cosmos_client'], #Cliente de Cosmos DB
                vector_embedding_policy=db_config['vector_embedding_policy'], #Política de embeddings
                indexing_policy=db_config['indexing_policy'], #Política de indexación
                cosmos_container_properties=db_config['cosmos_container_properties'], #Propiedades del contenedor
                cosmos_database_properties=db_config['cosmos_database_properties'], #Propiedades de la BD
                database_name=db_config.get('database_name', 'vectorSearchDB'), #Nombre de BD con valor por defecto
                container_name=db_config.get('container_name', 'vectorSearchContainer'), #Nombre de contenedor con valor por defecto
                create_container=db_config.get('create_container', False) #Flag para crear contenedor
            )
            logging.info(f"Vectorización completada exitosamente con {len(documents)} documentos") #Confirma éxito
        except KeyError as e: #Captura errores de claves faltantes
            logging.error(f"Error: Falta la clave '{e}' en db_config. No se puede completar la vectorización.") #Error específico
            raise
        except Exception as e: #Captura errores generales
            logging.error(f"Error inesperado durante la vectorización: {e}") #Error inesperado
            raise
        
        return cls(vectorstore) #Retorna instancia de la clase con vectorstore configurado

    def save_index(self, index_options=None): #Define método para guardar índice con opciones opcionales
        logging.info("Guardando índice en Azure Cosmos DB NoSQL") #Registra el inicio del proceso de guardado
        try:
            # No se necesita llamar a `create_index`, ya que el índice es manejado automáticamente por Cosmos DB
            logging.info("Índice guardado exitosamente en Azure Cosmos DB NoSQL (manejada automáticamente)") #Confirma el guardado exitoso
        except Exception as e: #Captura cualquier excepción durante el proceso
            logging.error(f"Error inesperado al guardar el índice: {e}") #Registra error con detalles
            raise

    def similarity_search_with_score(self, query, k=4): #Define método de búsqueda por similitud con puntuación, recibe consulta y número de resultados (k=4 por defecto)
        return self.vectorstore.similarity_search_with_score(query, k) #Delega la búsqueda al vectorstore subyacente y retorna resultados con puntuaciones

    def as_retriever(self): #Define método para obtener un retriever del vectorstore
        logging.info(f"obteniendo retrieve de CosmosDB") #Registra la operación de obtención del retriever
        return self.vectorstore.as_retriever()   #Retorna el retriever del vectorstore para uso en cadenas de LangChain  
    
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
    query = f"SELECT c.id, c.url, c.row_number, c.anio, c.titulo, c.des, c.tema, c.subtema, c.borrado FROM c WHERE c.id IN ({','.join(['"' + str(doc_id) + '"' for doc_id in doc_ids])})"

    try:
        items = container.query_items(query=query, enable_cross_partition_query=True)
        for item in items:
            metadata[item['id']] = {
                'url': item.get('url', 'Desconocido'),
                'row_number': item.get('row_number', 'Desconocido'),
                'anio': item.get('anio', 'Desconocido'),
                'titulo': item.get('titulo', 'Desconocido'),
                'desc': item.get('desc', 'Desconocido'),
                'tema': item.get('tema', 'Desconocido'),
                'subtema': item.get('subtema', 'Desconocido'),
                'borrado': item.get('borrado', False)  # Asumir 'False' si no existe
            }
    except Exception as e:
        logging.error(f"Error al consultar metadata adicional en Cosmos DB: {e}")

    return metadata

def get_all_cosmosdb_documents():
    """
    Función para leer todos los documentos del contenedor de Cosmos DB.
    """
    try:
        query = "SELECT distinct c.url, c.row_number, c.anio, c.titulo, c.des, c.tema, c.subtema, c.borrado FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not items:
            logging.info("No documents found in Cosmos DB")
            return {"message": "No documents found"}, 404

        logging.info(f"Documents retrieved: {len(items)}")
        return items, 200

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error fetching documents from Cosmos DB: {e.message}")
        return {"error": "Failed to fetch documents"}, 500
    
import requests

def get_max_row_number_for_new_service():
    """
    Consulta en Cosmos DB para obtener el valor máximo de `row_number` donde `new_service` es True.
    """
    query = "SELECT VALUE MAX(c.row_number) FROM c WHERE c.new_service = true"
    result = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not result:
        logging.info("No se encontraron documentos con new_service = true.")
        return None

    max_row_number = result[0]
    return max_row_number

def update_file(row_number, tipo:bool,info_usuario,razon_accion):
    """
    Marca como 'borrado' todos los documentos que coincidan con la URL basada en el 'row_number' y
    ejecuta el indexador de Azure Search para actualizar el índice.
    """
    try:
        # Paso 1: Consultar la URL basada en el row_number
        query_url = f"SELECT c.url FROM c WHERE c.row_number = {row_number}"
        result = list(container.query_items(query=query_url, enable_cross_partition_query=True))

        if not result:
            logging.info(f"No se encontró URL con el row_number: {row_number}")
            return {"error": "No se encontraron documentos con ese row_number"}, 404

        # Asumimos que el primer resultado contiene la URL que necesitamos
        url = result[0]['url']

        # Paso 2: Usar la URL para encontrar todos los documentos relacionados
        query_documents = f"SELECT * FROM c WHERE c.url = '{url}'"
        items = list(container.query_items(query=query_documents, enable_cross_partition_query=True))

        if not items:
            logging.info(f"No se encontraron documentos con la URL: {url}")
            return {"error": "No se encontraron documentos con esa URL"}, 404

        # Marcar borrado lógico en todos los documentos encontrados
        for document in items:
            document['borrado'] = tipo
            document['usuario_actualizacion']=info_usuario
            document['observacion_actualizacion']=razon_accion
            document['fecha_actualizacion'] = datetime.now(colombia_tz).isoformat() 
            container.upsert_item(body=document)  # Actualiza el documento en Cosmos DB
            logging.info(f"Documento con ID {document['id']} marcado como borrado.")

        return call_index_for_update_all()

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error al marcar como borrado: {e.message}")
        return {"error": f"Error al marcar como borrado: {e.message}"}, 500
    

def call_index_for_update_all():
    # Ejecutar el indexador de Azure Search después del borrado lógico
    indexer_name = os.getenv("AZURE_SEARCH_INDEXER")
    search_service_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexers/{indexer_name}/run?api-version=2021-04-30-Preview"
    api_key = os.getenv("AZURE_SEARCH_KEY")

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    response = requests.post(search_service_url, headers=headers)

    if response.status_code == 202:
        logging.info("Indexador de Azure Search ejecutado exitosamente.")
    else:
        error_message = f"Error al ejecutar el indexador de Azure Search: {response.status_code}, {response.text}"
        logging.error(error_message)
        raise Exception(error_message)

    return {"message": "Documentos marcados como borrados y el indexador se ejecutó exitosamente"}, 200