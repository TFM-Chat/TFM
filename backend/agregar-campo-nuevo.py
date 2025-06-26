from azure.cosmos import CosmosClient, exceptions
import os
from datetime import datetime

# Configuración de la conexión
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")

# Inicializa el cliente Cosmos
HOST = os.getenv('COSMOSDB_ENDPOINT')
KEY = os.getenv('COSMOSDB_KEY')
client = CosmosClient(HOST, KEY)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Obtener la fecha actual en el formato ISO 8601 (YYYY-MM-DD)
fecha_actual = datetime.now().strftime("%Y-%m-%d")

# Diccionario con los nuevos campos a agregar y sus valores
nuevos_campos = {
    "observacion_actualizacion": None,
    "usuario_creacion": "carga_inicial",
    "usuario_actualizacion": None,
    "fecha_creacion": fecha_actual,  # Usar la fecha actual
    "fecha_actualizacion": None  # Usar la fecha actual
}

# Realizar una consulta para traer solo el id de los documentos
query = "SELECT c.id FROM c WHERE NOT IS_DEFINED(c.observacion_actualizacion)"
items = list(container.query_items(query=query, enable_cross_partition_query=True))

for item in items:
    try:
        # Recuperar solo el id para actualizar el documento correspondiente
        document_id = item['id']

        # Obtener el documento actual por su ID, trayendo solo los campos necesarios para evitar cargar 'embedding'
        document = container.read_item(item=document_id, partition_key=document_id)

        # Agregar los nuevos campos al documento existente
        for campo, valor in nuevos_campos.items():
            document[campo] = valor

        # Actualizar el documento en Cosmos DB
        container.upsert_item(body=document)
        print(f"Documento con ID {document_id} actualizado exitosamente. Campos {list(nuevos_campos.keys())} agregados.")

    except exceptions.CosmosHttpResponseError as e:
        print(f"Error al actualizar el documento con ID {item['id']}: {e.message}")