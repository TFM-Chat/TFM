import requests
import os

indexer_name = os.getenv("AZURE_SEARCH_INDEXER")
search_service_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexers/{indexer_name}/run?api-version=2021-04-30-Preview"
api_key = os.getenv("AZURE_SEARCH_KEY")
url = os.getenv("AZURE_SEARCH_ENDPOINT")


# Cabecera para la petición
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

# Cuerpo de la petición
data = {
    "value": [
        {
            "@search.action": "delete",
            "url": url  # Reemplaza por el campo clave de tu índice
        }
    ]
}

# Realizar la solicitud
response = requests.post(search_service_url, json=data, headers=headers)

# Revisar la respuesta
if response.status_code == 200:
    print("Documento eliminado correctamente del índice de Azure Search")
else:
    print(f"Error al eliminar el documento: {response.status_code}, {response.text}")