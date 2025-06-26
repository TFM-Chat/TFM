import os
import time
import logging
from services.vectorize_service import vectorize_and_save
from services.metadata_service import load_metadata, save_metadata
from vectorstores.factory import get_vectorstore
from dotenv import load_dotenv
from services.model_service import get_embeddings

def vectorize_documents(document_folder, metadata_path): #Define la función con parámetros document_folder (carpeta de documentos) y metadata_path (ruta de metadatos)
    embeddings = get_embeddings()  # Obtener los embeddings usando la función definida
    logging.info('Iniciando proceso de verificación para vectorización') #Registra el inicio del proceso de verificación para vectorización

    document_paths = [os.path.join(document_folder, f) for f in os.listdir(document_folder) if f.lower().endswith(('.pdf', '.xlsx', '.xls'))] #Crea una lista de rutas de documentos filtrando archivos con extensiones PDF, XLSX y XLS
    logging.info(f'Documentos encontrados para procesar: {document_paths}') #Registra la cantidad de documentos encontrados para procesamiento

    timestamps = [os.path.getmtime(path) for path in document_paths] #Obtiene los timestamps de modificación de cada archivo encontrado
    metadata = load_metadata(metadata_path) #Carga los metadatos existentes desde el archivo especificado

    existing_paths = metadata["paths"] #Extrae las rutas de documentos previamente procesados desde los metadatos
    existing_timestamps = metadata["timestamps"] #Extrae los timestamps de procesamiento previo
    to_vectorize = [] #Inicializa lista para documentos que requieren vectorización
    new_timestamps = [] #Inicializa lista para nuevos timestamps

    for path, timestamp in zip(document_paths, timestamps): #tera sobre cada documento y su timestamp correspondiente
        if path not in existing_paths or timestamp != existing_timestamps[existing_paths.index(path)]: #Verifica si el documento es nuevo o si su timestamp ha cambiado
            logging.info(f'Documento para vectorizar: {path}') #Registra el documento que será vectorizado
            to_vectorize.append(path) #Añade el documento a la lista de vectorización
            new_timestamps.append(timestamp) #Añade el nuevo timestamp a la lista correspondiente

    removed_docs = [path for path in existing_paths if path not in document_paths] #Identifica documentos que fueron eliminados del directorio
    logging.info(f'Documentos eliminados de la vectorización: {removed_docs}') #Registra la cantidad de documentos eliminados de la vectorización

    # Dividir la lista de documentos a vectorizar en lotes de 50
    batch_size = 50 #Define el tamaño del lote en 50 documentos
    total_batches = (len(to_vectorize) + batch_size - 1) // batch_size  # Calcula el número total de lotes
    tiempo_espera=20 #Establece un tiempo de espera de 20 segundos entre lotes
    for batch_num in range(total_batches): #Inicia un bucle para procesar cada lote numerado
        start_idx = batch_num * batch_size #Calcula el índice de inicio del lote actual
        end_idx = min(start_idx + batch_size, len(to_vectorize)) #Determina el índice final del lote usando el mínimo entre el cálculo y la longitud total
        batch_paths = to_vectorize[start_idx:end_idx] #Extrae las rutas de documentos correspondientes al lote actual
        batch_timestamps = new_timestamps[start_idx:end_idx] #Obtiene los timestamps correspondientes a los documentos del lote

        if batch_paths: #Verifica si existen documentos en el lote actual
            embeddings_start_time = time.time() #Registra el tiempo de inicio de la vectorización
            logging.info(f'Comienzo de la vectorización para lote {batch_num + 1}/{total_batches}') #Registra información sobre el lote que se está procesando
            vectorstore = vectorize_and_save(batch_paths, batch_timestamps, embeddings, metadata_path) #Ejecuta la función de vectorización y almacenamiento para el lote
            embeddings_end_time = time.time() #Registra el tiempo de finalización de la vectorización
            embeddings_time_taken = embeddings_end_time - embeddings_start_time #Calcula el tiempo total transcurrido en el procesamiento
            logging.info(f'Fin de la vectorización para lote {batch_num + 1}/{total_batches}, tiempo tomado: {embeddings_time_taken} segundos') #Registra información sobre la finalización del lote con el tiempo empleado

            # Pausa segundos entre lotes
            logging.info(f'Esperando {tiempo_espera} segundos antes de procesar el siguiente lote...') #Registra mensaje informativo sobre la pausa
            time.sleep(tiempo_espera) #Ejecuta la pausa por el tiempo especificado

    updated_paths = [path for path in document_paths if path not in removed_docs] #Filtra las rutas actualizadas excluyendo documentos eliminados
    updated_timestamps = [timestamps[document_paths.index(path)] for path in updated_paths] #Actualiza los timestamps correspondientes a las rutas filtradas
    save_metadata(metadata_path, {"paths": updated_paths, "timestamps": updated_timestamps}) #Guarda los metadatos actualizados con las nuevas rutas y timestamps
    logging.info('Metadata actualizada y guardada') #Registra la finalización del proceso de actualización de metadatos

    return vectorstore #Devuelve el objeto vectorstore resultante del procesamiento

if __name__ == "__main__":
    load_dotenv()  # Cargar las variables de entorno desde un archivo .env
    document_folder = os.getenv("CARPETA_DOCUMENTOS")
    metadata_path = f"metadata_{os.getenv('MODELO')}.json"

    try:
        vectorstore = vectorize_documents(document_folder, metadata_path)
        logging.info("Vectorización completada correctamente.")
    except RuntimeError as e:
        logging.error(f"Error en la vectorización: {e}")