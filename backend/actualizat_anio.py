import pandas as pd
from azure.cosmos import CosmosClient
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

def update_year_in_cosmos():
    try:
        # Ruta local del archivo Excel
        excel_path = "anio_update.xlsx"  # Cambia esta ruta si es necesario
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"El archivo Excel no se encontró en la ruta: {excel_path}")

        # Leer el archivo Excel
        df = pd.read_excel(excel_path)

        # Validar que las columnas necesarias existen
        required_columns = ["adjunto", "anio"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"El archivo Excel debe contener las columnas: {', '.join(required_columns)}.")

        # Iterar sobre cada fila del Excel y actualizar Cosmos DB
        results = []
        for index, row in df.iterrows():
            url = row["adjunto"]
            new_year = row["anio"]

            try:
                # Query para buscar los documentos por URL
                query = f"SELECT * FROM c WHERE c.titulo = '{url}' AND c.usuario_creacion = 'carga_nuevos'"
                items = list(container.query_items(query=query, enable_cross_partition_query=True))

                if not items:
                    raise ValueError(f"No se encontraron documentos con la URL: {url}")

                # Iterar sobre todos los documentos encontrados y actualizar el año
                for document in items:
                    document_id = document["id"]
                    partition_key = document["id"]  # Cambia esto si usas otra clave de partición

                    # Actualizar solo el campo `anio`
                    document["anio"] = new_year

                    # Reemplazar el documento actualizado
                    container.replace_item(item=document_id, body=document)

                results.append({
                    "url": url,
                    "status": "success",
                    "message": f"Se actualizaron {len(items)} documentos con el nuevo año."
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "status": "error",
                    "message": str(e)
                })

        return results

    except Exception as e:
        print(f"Error al actualizar años: {str(e)}")
        return []

# Ejecutar la función de actualización
if __name__ == "__main__":
    update_results = update_year_in_cosmos()
    for result in update_results:
        print(result)