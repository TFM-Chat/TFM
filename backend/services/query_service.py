import os
import time
import tiktoken
from services.vectorize_service import vectorize_and_save
from services.metadata_service import load_metadata, save_metadata
from services.retrieval_service import create_retrieval_chain_service
from vectorstores.cosmosdb_store import query_cosmosdb_for_metadata, get_all_cosmosdb_documents, update_file, get_max_row_number_for_new_service, call_index_for_update_all
from vectorstores.factory import get_vectorstore
import logging
from logging_module.logging_config import setup_logging

def adapt_similarity_search_with_score_results(results):
    adapted_results = []
    for doc, score in results:
        score = float(score)
        doc.metadata['score'] = score
        adapted_results.append(doc)
    return adapted_results

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text))

def handle_query(question, get_llm, get_embeddings):
    logging.info('Inicio del proceso de manejo de la consulta')
    
    llm = get_llm()
    embeddings_time_taken = "No se realizó embeddings ya que toda la información está vectorizada en la BD"
    embeddings = get_embeddings()
    try:
        store_type = os.getenv('VECTORSTORE_TYPE', 'FAISS')
        vectorstore = get_vectorstore(store_type, "vector_index_" + os.getenv('MODELO'), embeddings)
        logging.info('Vectorstore cargado exitosamente')
    except RuntimeError as e:
        logging.error(f"Error al cargar el vectorstore: {e}")
        return {"error": f"Error loading vectorstore: {e}"}, 500


    if not vectorstore:
        logging.error("No vectorstore disponible")
        return {"error": "No vectorstore available"}, 500

    retrieval_chain = create_retrieval_chain_service(llm, vectorstore)
    if not retrieval_chain:
        logging.error("Error al crear la cadena de recuperación")
        return {"error": "Error creating retrieval chain"}, 500

    num_results = 4
    logging.info('Iniciando búsqueda de similaridad')
    retrieved_docs_with_scores = vectorstore.similarity_search_with_score(question, k=num_results)
    
    # Extraer los IDs de los documentos recuperados
    retrieved_doc_ids = [doc.metadata.get('id') for doc, score in retrieved_docs_with_scores]

    # Realizar una consulta personalizada a Cosmos DB para obtener metadata adicional
    ##additional_metadata = query_cosmosdb_for_metadata(retrieved_doc_ids)

    logging.info(f'Búsqueda de similaridad completada, resultados obtenidos: {len(retrieved_docs_with_scores)}')

    logging.info('Adaptando resultados de búsqueda de similaridad')
    retrieved_docs = adapt_similarity_search_with_score_results(retrieved_docs_with_scores)
    logging.info('Adaptación de resultados completada')

    tokenizer = tiktoken.get_encoding("cl100k_base")  # Asegúrate de usar el tokenizador adecuado para tu modelo

    question_tokens = count_tokens(question, tokenizer)
    docs_tokens = sum(count_tokens(doc.page_content, tokenizer) for doc in retrieved_docs)
    logging.info(f'Tokens en la pregunta: {question_tokens}, Tokens en los documentos: {docs_tokens}')

    query_start_time = time.time()
    
    logging.info('Iniciando consulta al modelo2')
    # Imprimir todos los row_number de los documentos
    
    
    
    
    
    response_data = {"Documentos_recuperados": []}

    # Llenar response_data con la información de los documentos recuperados
    seen_url = set()  # Conjunto para rastrear URLs ya procesadas
    for doc in retrieved_docs:
        doc_id = doc.metadata.get('id', 'Desconocido')
        #metadata_add = additional_metadata.get(doc_id, {})
        
        # Construir la información de los documentos recuperados
        # Verificar si la URL ya fue procesada
        pdf_url=doc.metadata.get('url', 'Desconocido')
        if pdf_url not in seen_url:
            seen_url.add(pdf_url)  # Añadir la URL al conjunto si es nueva
            response_data["Documentos_recuperados"].append({
                'PDF': doc.metadata.get('url', 'Desconocido'),
                'timestamp': doc.metadata.get('timestamp', 'Desconocido'),
                'contenido': doc.page_content,
                'score': doc.metadata.get('score', 'N/A'),
                'row_number': doc.metadata.get('row_number', 'Desconocido'),
                'anio': doc.metadata.get('anio', 'Desconocido'),
                'titulo': doc.metadata.get('titulo', 'Desconocido'),
                'desc': doc.metadata.get('desc', 'Desconocido'),
                'tem': doc.metadata.get('tema', 'Desconocido'),
                'subtema': doc.metadata.get('subtema', 'Desconocido'),
                'borrado': doc.metadata.get('borrado', False)  # Asume False si no existe
            })

    # Filtrar los documentos en response_data que tienen 'row_number' igual a 'Desconocido'
    response_data["Documentos_recuperados"] = [doc for doc in response_data["Documentos_recuperados"] if doc['row_number'] != 'Desconocido']

    logging.info(f'Número de documentos válidos después del filtrado: {len(response_data["Documentos_recuperados"])}')

        # Crear la lista info_buscar con el contenido de los documentos que pasaron el filtro
    info_buscar = [
    f"Tema: {doc['tem']}, Subtema: {doc['subtema']}, Descripción: {doc['desc']}, Año: {doc['anio']}, Título: {doc['titulo']}.\nContenido: {doc['contenido']}" 
    for doc in response_data["Documentos_recuperados"]
]
    # Verificar si info_buscar está vacío justo antes de la invocación
    resYesNo="No"
    if len(info_buscar) == 0:
        # Si no hay contexto, devolver una respuesta predeterminada
        res = {"answer": "No se encontro una respuesta de acuerdo a la pregunta realizada"}
    else:
        # Si hay contexto, realizar la consulta al modelo
        res = retrieval_chain.invoke({"context": info_buscar, "input": question+". recuerda que solo puedes contestar si esta en el contexto la respuesta, pero no meciones la palabra contexto"})
        resYesNo = retrieval_chain.invoke({"input": "Dado el siguiente texto: "+res["answer"]+", responde solo con 'sí' si el texto afirma que se encontró la respuesta solicitada. Responde 'no' si el texto indica que no se encontró la respuesta. No agregues nada más."})
    
    if resYesNo["answer"].lower() == "no":
        res = {"answer": "No se encontro una respuesta de acuerdo a la pregunta realizada"}
        response_data["Documentos_recuperados"]=[]
    query_end_time = time.time()
    query_time_taken = query_end_time - query_start_time
    logging.info(f'Consulta al modelo completada, tiempo tomado: {query_time_taken} segundos')

    response_tokens = count_tokens(res["answer"], tokenizer)
    logging.info(f'Tokens en la respuesta: {response_tokens}')

    # Actualizar response_data con la respuesta final y la información de tiempo y tokens
    response_data.update({
        "Pregunta": question,
        "Respuesta": res["answer"],
        "Modelo_usado": os.getenv('MODELO'),
        "Tiempo_embeddings": embeddings_time_taken,
        "Tiempo_consulta_modelo": query_time_taken,
        "Tokens_pregunta": question_tokens,
        "Tokens_documentos": docs_tokens,
        "Tokens_respuesta": response_tokens
    })

    logging.info('Proceso de manejo de la consulta completado')
    return response_data

def query_all_docs():
    return get_all_cosmosdb_documents()

def get_max_row_number_ns():
    return get_max_row_number_for_new_service()

def update_file_principal(row_number, tipo:bool, info_usuario,razon_accion):
    return update_file(row_number, tipo, info_usuario,razon_accion)

def call_index_for_update():
    return call_index_for_update_all()
