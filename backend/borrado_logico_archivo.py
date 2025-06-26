from azure.cosmos import CosmosClient, exceptions
import os
from datetime import datetime, timedelta, timezone

# Configuración de la conexión
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")

# Inicializa el cliente Cosmos
HOST = os.getenv('COSMOSDB_ENDPOINT')
KEY = os.getenv('COSMOSDB_KEY')
client = CosmosClient(HOST, KEY)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Lista de 'row_number' a buscar para marcar borrado lógico
row_numbers_to_update = [3447, 3449, 3449, 3449, 3449, 3449, 3448, 3449, 3447, 3449, 3448, 3449, 3449, 3448, 3449, 3449, 3449, 3447, 3449, 3448, 3449, 3449, 3447, 3449, 3449, 3447, 3448, 3449, 3449, 3449]  # Reemplaza con tus 'row_number' específicos

try:
    # Convertir la lista de 'row_number' a una cadena para la consulta
    row_numbers_str = ', '.join(map(str, row_numbers_to_update))
    
    # Consultar todos los documentos que coincidan con los 'row_number' especificados
    query = f"SELECT * FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        print(f"No se encontraron documentos con los row_numbers: {row_numbers_to_update}")
    else:
        for document in items:
            # Modificar los campos según lo solicitado
            document['borrado'] = True
            document['usuario_creacion'] = "solicitud_eliminacion"
            document['usuario_actualizacion'] = "12345678||KAREN LILIANA REYES REYES||167345"
            
            # Definir la zona horaria con el offset de -05:00
            tz = timezone(timedelta(hours=-5))
            # Obtener la fecha actual en el formato especificado
            document['fecha_actualizacion'] = datetime.now(tz).isoformat()
            
            document['observacion_actualizacion'] = "Registros eliminados por que son de pruebas"

            # Actualizar el documento en Cosmos DB
            container.upsert_item(body=document)
            print(f"Documento con ID {document['id']} actualizado exitosamente.")

except exceptions.CosmosHttpResponseError as e:
    print(f"Error al actualizar el documento: {e.message}")