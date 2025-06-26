import os
from datetime import datetime
import logging
from logging_module.logging_config import setup_logging
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredExcelLoader, AzureAIDocumentIntelligenceLoader
from langchain_text_splitters import CharacterTextSplitter
from services.model_service import get_embeddings_option_2
from vectorstores.factory import get_vectorstore_class
from services.metadata_service import save_metadata
from azure.cosmos import CosmosClient, exceptions
import json
from langchain_core.documents import Document
from config.db_cosmos_config import db_config
from config.db_cosmos_config_option_2 import db_config_option_2

# Configurar logging
setup_logging()

def load_all_documents_from_cosmosdb(paths):
    # Conectar a Cosmos DB
    endpoint = os.getenv('COSMOSDB_ENDPOINT')
    key = os.getenv('COSMOSDB_KEY')
    client = CosmosClient(endpoint, key)
    
    database_name = os.getenv('COSMOSDB_DATABASE')
    container_name = os.getenv('COSMOSDB_CONTAINER_VECTOR')
    
    all_documents = []
    
    try:
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        for path in paths:
            query = f"SELECT c.id,c.text,c.source,c.file_size,c.chunk_index,c.row_number,c.url FROM c WHERE c.source = '{path}'"
            
            documents = list(container.query_items(query, enable_cross_partition_query=True))
            all_documents.extend(documents)
            
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error al conectar o leer desde CosmosDB: {str(e)}")
    
    return all_documents

def vectorize_and_save(paths, timestamps, embeddings, metadata_path):
    all_docs = []
    count_intelligence = 0
    emebedding_selected=embeddings
    db_config_vectorize=db_config
    
    # Cargar la ruta de la carpeta de metadatos desde el archivo .env
    carpeta_documentos_metadata = os.getenv("CARPETA_DOCUMENTOS_METADATA")
    use_cosmosdb = os.getenv('USE_ALTERNATIVE', 'false').lower() == 'true'
    if use_cosmosdb:
        db_config_vectorize=db_config_option_2
        emebedding_selected=get_embeddings_option_2()
        logging.info("Usando Cosmos DB para cargar todos los documentos.")

        # Cargar todos los documentos de Cosmos DB de una sola vez
        documents_from_db = load_all_documents_from_cosmosdb(paths)
        
        for doc in documents_from_db:
            try:
                # Extraer el contenido y metadatos del documento
                content = doc.get('text', '')
                source = doc.get('source', '')
                file_size = doc.get('file_size', None)
                chunk_index = doc.get('chunk_index', None)
                row_number = doc.get('row_number', None)
                url = doc.get('url', None)
                
                if not content:
                    continue

                # Crear documento directamente ya que no se requiere procesamiento adicional
                new_doc = Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "file_size": file_size,
                        "chunk_index": chunk_index,
                        "row_number": row_number,
                        "url": url
                    }
                )
                
                all_docs.append(new_doc)
            
            except Exception as e:
                logging.error(f"Error procesando documento de CosmosDB: {e}")
    
    else:
        for path, timestamp in zip(paths, timestamps):
            try:
                # Determinar el tamaño del archivo
                file_size = os.path.getsize(path)
                
                # Construir el nombre del archivo de metadatos asociado
                base_name = os.path.splitext(os.path.basename(path))[0]  # Obtener el nombre base sin extensión
                metadata_file_path = os.path.join(carpeta_documentos_metadata, base_name + ".json")

                # Verificar si el archivo de metadatos existe y cargarlo
                if os.path.exists(metadata_file_path):
                    with open(metadata_file_path, 'r') as metadata_file:
                        metadata_content = json.load(metadata_file)
                        row_number = metadata_content.get("row_number", None)
                        url = metadata_content.get("url", None)
                else:
                    row_number = None
                    url = None

                if path.lower().endswith('.pdf'):
                    logging.info(f'Inicio con documentIntelligence numero:{count_intelligence}')  
                    count_intelligence += 1
                    endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
                    key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
                    api_model_id = os.getenv("DOCUMENT_INTELLIGENCE_MODEL")
                    loader = AzureAIDocumentIntelligenceLoader(
                        api_endpoint=endpoint, 
                        api_key=key, 
                        file_path=path, 
                        api_model=api_model_id
                    )
                elif path.lower().endswith('.xlsx') or path.lower().endswith('.xls') or path.lower().endswith('.txt'):
                    logging.info('Carga xls/txt con UnstructuredExcelLoader: ' + path)
                    loader = UnstructuredExcelLoader(file_path=path, mode="elements")
                    logging.info('Fin Carga xls/txt con UnstructuredExcelLoader: ' + path)  
                else:
                    logging.info(f'Este path no fue cargado por no econtrar una extensión válida: {path}')   
                    continue

                logging.info('Iniciando loader:' + path)
                
                documents = loader.load()
                logging.info('Fin loader:' + path)
                logging.info(f'Documento cargado contiene {len(documents)} elementos')

                # Verificar los documentos cargados antes de dividirlos
                for doc in documents:
                    logging.info(f'Contenido del documento antes del split: {doc.page_content[:200]}...')  # Mostrar primeros 200 caracteres

                chunk_size = int(os.getenv('CHUNK_SIZE'))
                chunk_overlap = int(os.getenv('CHUNK_OVERLAP'))
                separator = '\n'
                logging.info(f'Iniciando creación Character splitter con chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, separator="{separator}": ' + path)
                
                text_splitter = CharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separator='\n'
                )
                
                logging.info('Fin creación Character splitter:' + path)
                logging.info('Iniciando splitter:' + path)
                docs = text_splitter.split_documents(documents=documents)
                logging.info(f'Fin splitter: {path}. Número de fragmentos creados: {len(docs)}')

                # Asignar metadatos adicionales a cada fragmento
                for idx, doc in enumerate(docs):
                    logging.info(f'Fragmento {idx + 1}/{len(docs)}: {doc.page_content[:200]}...')  # Mostrar primeros 200 caracteres del fragmento
                    doc.metadata["source"] = path
                    doc.metadata["timestamp"] = timestamp
                    doc.metadata["file_size"] = file_size
                    doc.metadata["chunk_index"] = idx + 1  # Índice del chunk (comienza en 1)
                    doc.metadata["row_number"] = row_number
                    doc.metadata["url"] = url

                all_docs.extend(docs)
            except Exception as e:
                logging.error(f"Error loading {path}: {e}")

    if not all_docs:
        logging.info("No documents to vectorize.")
        return None

    store_class = get_vectorstore_class(os.getenv('VECTORSTORE_TYPE', 'FAISS'))
    # Log the number of documents to be vectorized
    logging.info(f"Number of documents to be vectorized: {len(all_docs)}")
    logging.info(f"Inicio Vectorizando todos los documentos....")
    vectorstore = store_class.from_documents(all_docs, emebedding_selected, db_config_vectorize)
    logging.info(f"Fin Vectorizando todos los documentos....")
    logging.info(f"Creando índice: " + "vector_index_" + os.getenv('MODELO'))
    vectorstore.save_index("vector_index_" + os.getenv('MODELO'))
    logging.info(f"Guardando metadata: " + metadata_path)
    save_metadata(metadata_path, {"timestamps": timestamps, "paths": paths})

    return vectorstore