import logging
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from logging_module.logging_config import setup_logging
from langchain.prompts import ChatPromptTemplate

# Configurar logging
setup_logging()

def create_retrieval_chain_service(llm, vectorstore):
    # Definir el prompt directamente en el código
    retrieval_qa_chat_prompt = ChatPromptTemplate.from_template(
        """
        SYSTEM
        Answer any user questions based solely on the context below:

        <context>
        {context}
        </context>

        PLACEHOLDER: chat_history

        HUMAN: {input}
        """
    )

    # Crear la cadena de documentos combinados
    combine_docs_chain = create_stuff_documents_chain(
        llm, retrieval_qa_chat_prompt
    )
    
    if vectorstore is None:
        logging.error("Error: Vectorstore no se ha creado correctamente.")
        return None

    # Crear la cadena de recuperación
    retrieval_chain = create_retrieval_chain(
        vectorstore.as_retriever(), combine_docs_chain
    )
    return retrieval_chain
