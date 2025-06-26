from azure.cosmos import CosmosClient
import os
url = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")


# Crear el cliente de Cosmos DB
client = CosmosClient(url, credential=key) #Crea una instancia del cliente de Cosmos DB utilizando la URL y las credenciales
database = client.get_database_client(database_name) #Obtiene una referencia a la base de datos específica
container = database.get_container_client(container_name) #Obtiene una referencia al contenedor que almacena los vectores

# Obtener el documento
document_id = "a90df531-c185-4894-bfdb-9f58ad47e9d3" #Define un ID específico de documento para la búsqueda
query = f"SELECT c.embedding FROM c WHERE c.id = '{document_id}'" #Construye una consulta SQL para seleccionar el campo de embedding basado en el ID del documento
items = list(container.query_items(query=query, enable_cross_partition_query=True)) #Ejecuta la consulta en el contenedor con particionamiento cruzado habilitado

# Obtener el vector y calcular su longitud
if items: #Verifica si se obtuvieron elementos de la consulta
    embedding = items[0]['embedding'] #Extrae el embedding del primer elemento encontrado
    vector_length = len(embedding) #Calcula la longitud del vector de embedding
    print(f"El vector tiene {vector_length} dimensiones.") #Muestra la dimensionalidad del vector encontrado
else:
    print("No se encontró el documento.") #Maneja el caso cuando no se encuentra el documento solicitado