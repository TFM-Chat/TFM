import os
import time
import logging
from services.vectorize_service import vectorize_and_save
from services.metadata_service import load_metadata, save_metadata
from vectorstores.factory import get_vectorstore
from dotenv import load_dotenv
from services.model_service import get_embeddings

def vectorize_documents(document_folder, metadata_path):
    embeddings = get_embeddings()  # Obtener los embeddings usando la función definida
    logging.info('Iniciando proceso de verificación para vectorización')

    document_paths = [os.path.join(document_folder, f) for f in os.listdir(document_folder) if f.lower().endswith(('.pdf', '.xlsx', '.xls'))]
    logging.info(f'Documentos encontrados para procesar: {document_paths}')

    timestamps = [os.path.getmtime(path) for path in document_paths]
    metadata = load_metadata(metadata_path)

    existing_paths = metadata["paths"]
    existing_timestamps = metadata["timestamps"]
    to_vectorize = []
    new_timestamps = []

    for path, timestamp in zip(document_paths, timestamps):
        if path not in existing_paths or timestamp != existing_timestamps[existing_paths.index(path)]:
            logging.info(f'Documento para vectorizar: {path}')
            to_vectorize.append(path)
            new_timestamps.append(timestamp)

    removed_docs = [path for path in existing_paths if path not in document_paths]
    logging.info(f'Documentos eliminados de la vectorización: {removed_docs}')

    # Dividir la lista de documentos a vectorizar en lotes de 50
    batch_size = 50
    total_batches = (len(to_vectorize) + batch_size - 1) // batch_size  # Calcula el número total de lotes
    tiempo_espera=20
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(to_vectorize))
        batch_paths = to_vectorize[start_idx:end_idx]
        batch_timestamps = new_timestamps[start_idx:end_idx]

        if batch_paths:
            embeddings_start_time = time.time()
            logging.info(f'Comienzo de la vectorización para lote {batch_num + 1}/{total_batches}')
            vectorstore = vectorize_and_save(batch_paths, batch_timestamps, embeddings, metadata_path)
            embeddings_end_time = time.time()
            embeddings_time_taken = embeddings_end_time - embeddings_start_time
            logging.info(f'Fin de la vectorización para lote {batch_num + 1}/{total_batches}, tiempo tomado: {embeddings_time_taken} segundos')

            # Pausa segundos entre lotes
            logging.info(f'Esperando {tiempo_espera} segundos antes de procesar el siguiente lote...')
            time.sleep(tiempo_espera)

    updated_paths = [path for path in document_paths if path not in removed_docs]
    updated_timestamps = [timestamps[document_paths.index(path)] for path in updated_paths]
    save_metadata(metadata_path, {"paths": updated_paths, "timestamps": updated_timestamps})
    logging.info('Metadata actualizada y guardada')

    return vectorstore

if __name__ == "__main__":
    load_dotenv()  # Cargar las variables de entorno desde un archivo .env
    document_folder = os.getenv("CARPETA_DOCUMENTOS")
    metadata_path = f"metadata_{os.getenv('MODELO')}.json"

    try:
        vectorstore = vectorize_documents(document_folder, metadata_path)
        logging.info("Vectorización completada correctamente.")
    except RuntimeError as e:
        logging.error(f"Error en la vectorización: {e}")