import os
import requests
import pandas as pd
import hashlib
import json
from urllib.parse import urlparse

# Ruta del archivo Excel y la carpeta de destino
excel_file = "infraestructura.xlsx"
output_folder = os.getenv("CARPETA_DOCUMENTOS")
metadata_folder = os.getenv("CARPETA_DOCUMENTOS_METADATA")

# Crear las carpetas de destino si no existen
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if not os.path.exists(metadata_folder):
    os.makedirs(metadata_folder)

# Leer el archivo Excel
df = pd.read_excel(excel_file)

# Función para obtener un nombre único basado en la URL
def generate_unique_filename(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()  # Crear un hash MD5 de la URL
    parsed_url = urlparse(url)
    file_extension = os.path.splitext(parsed_url.path)[1]  # Obtener la extensión del archivo
    return f"{url_hash}{file_extension}"

# Columna 6 para URL (columna F, índice 5) y columna 8 para estado de descarga (columna H, índice 7)
url_column_index = 5
status_column_index = 7

# Asegúrate de que la columna de estado de descarga exista
if df.shape[1] <= status_column_index:
    df.insert(status_column_index, "Descargado", "")

# Iterar sobre los enlaces en la columna correspondiente
for index, row in df.iterrows():
    url = row.iloc[url_column_index]
    
    if pd.isna(url):
        print(f"No se encontró URL en la fila {index + 1}.")
        continue

    # Generar un nombre de archivo único
    file_name = generate_unique_filename(url)
    file_path = os.path.join(output_folder, file_name)
    metadata_path = os.path.join(metadata_folder, os.path.splitext(file_name)[0] + ".json")

    # Verificar si el archivo ya existe
    if os.path.exists(file_path):
        try:
            # Descargar temporalmente la cabecera del archivo para verificar su tamaño
            response = requests.head(url)
            file_size = int(response.headers.get('Content-Length', 0))
            
            # Verificar el tamaño del archivo
            if os.path.getsize(file_path) == file_size:
                print(f"El archivo {file_name} ya existe y tiene el mismo tamaño. Marcando como 'No modificado'.")
                df.iat[index, status_column_index] = "No modificado"
                
                # Guardar metadatos
                metadata = {
                    "url": url,
                    "row_number": index + 1
                }
                with open(metadata_path, 'w') as metadata_file:
                    json.dump(metadata, metadata_file)

                continue
        except requests.exceptions.RequestException as e:
            print(f"Error al verificar el archivo en {url}: {e}")
            df.iat[index, status_column_index] = f"Error: {e}"
            continue

    try:
        # Descargar el archivo si no existe o si es diferente
        response = requests.get(url)
        response.raise_for_status()  # Levantar excepción si la descarga falla

        # Guardar el archivo en la carpeta de destino
        with open(file_path, 'wb') as file:
            file.write(response.content)

        print(f"Descargado y guardado: {file_name} este archivo: {url} y este index: {index}")
        df.iat[index, status_column_index] = "Descargado"

        # Guardar metadatos
        metadata = {
            "url": url,
            "row_number": index + 1
        }
        with open(metadata_path, 'w') as metadata_file:
            json.dump(metadata, metadata_file)

    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo de {url}: {e}")
        df.iat[index, status_column_index] = f"Error: {e}"

# Guardar los cambios en el archivo Excel
df.to_excel(excel_file, index=False)
print("Proceso de descarga completado y Excel actualizado.")