import pandas as pd
from azure.cosmos import CosmosClient, PartitionKey
import os

url = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE")
container_name = os.getenv("COSMOSDB_CONTAINER_VECTOR")



# Inicializar cliente de Cosmos
client = CosmosClient(url, key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Cargar el archivo Excel/CSV
file_path = 'infraestructura.xlsx'  # Cambia a la ruta de tu archivo
df = pd.read_excel(file_path)

# Iterar sobre cada fila del archivo Excel
for index, row in df.iterrows():
    # Obtener los valores del archivo Excel
    row_number = index+1 # Suponiendo que row_number empieza en 1
    anio = row['anio']
    titulo = row['titulo']
    desc = row['desc']
    tema = row['tema']
    subtema = row['subtema']
    
    # Buscar el documento en Cosmos DB usando el row_number
    query = f"SELECT * FROM c WHERE c.row_number = {row_number}"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    val_id=''
    
    if items:
        # Iterar sobre cada elemento encontrado
        for item in items:
            # Convertir el campo 'anio' a un string (formato 'YYYY-MM-DD')
            # Convertir el campo 'anio' a un string (formato 'YYYY-MM-DD') o manejar NaN
            item['anio'] = anio.strftime('%Y-%m-%d') if isinstance(anio, pd.Timestamp) else (None if pd.isna(anio) else anio)

            # Manejar NaN en los demás campos
            item['titulo'] = None if pd.isna(titulo) else titulo
            item['desc'] = None if pd.isna(desc) else desc
            item['tema'] = None if pd.isna(tema) else tema
            item['subtema'] = None if pd.isna(subtema) else subtema
            item['borrado'] = False

            # Eliminar campos reservados
            reserved_fields = ['_rid', '_self', '_etag', '_attachments', '_ts']
            for field in reserved_fields:
                if field in item:
                    del item[field]

            # Reemplazar el documento actualizado en Cosmos DB
            container.replace_item(item=item['id'], body=item)
            print(f"Documento con row_number {row_number} actualizado.")
    else:
        print(f"Documento con row_number {row_number} no encontrado.")