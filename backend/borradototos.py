import os
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de Cosmos DB desde el archivo .env
url = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")

# Conexión al cliente de Cosmos DB
client = CosmosClient(url, credential=key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Consulta para seleccionar todos los documentos
query = "SELECT * FROM c where c.new_service=true"

# Borrar cada documento
for item in container.query_items(query=query, enable_cross_partition_query=True):
    try:
        #partition_key_value = item.get('partitionKey', 'None')
        #if partition_key_value is None:
        #    print(f"El documento con id: {item['id']} no tiene un partitionKey definido, omitiendo eliminación.")
        #    continue

        container.delete_item(item['id'], partition_key=item['id'])
        print(f"Eliminado el documento con id: {item['id']} y partitionKey: {item['id']}")
    except exceptions.CosmosResourceNotFoundError:
        print(f"Documento con id: {item['id']} no encontrado o ya eliminado.")
    except Exception as e:
        print(f"Ocurrió un error al intentar eliminar el documento con id: {item['id']}. Error: {e}")

print("Todos los registros posibles han sido procesados para eliminación.")