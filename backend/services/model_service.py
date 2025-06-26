from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
import logging
from logging_module.logging_config import setup_logging

# Configurar logging
setup_logging()

load_dotenv()

def get_embeddings():
    if os.getenv('MODELO') == "llama":
        logging.info('Using Ollama embeddings for llama')
        return OllamaEmbeddings(model="llama3.1")
    else:
        logging.info('Using Azure OpenAI embeddings')
        return AzureOpenAIEmbeddings(
            model=os.getenv('OPEN_AI_EMBEDDING_MODEL'), 
            azure_deployment=os.getenv('OPEN_AI_EMBEDDING_DEPLOYMENT')
        )
    
def get_embeddings_option_2():
    if os.getenv('MODELO') == "llama":
        logging.info('Using Ollama embeddings for llama')
        return OllamaEmbeddings(model="llama3.1")
    else:
        logging.info('Using Azure OpenAI embeddings')
        return AzureOpenAIEmbeddings(
            model=os.getenv('OPEN_AI_EMBEDDING_MODEL_OPTION_2'), 
            azure_deployment=os.getenv('OPEN_AI_EMBEDDING_DEPLOYMENT_OPTION_2')
        )   

def get_llm():
    if os.getenv('MODELO') == "llama":
        logging.info('Using ChatOllama for llama')
        return ChatOllama(model=os.getenv("LLAMA_VERSION"))
    else:
        logging.info('Using Azure OpenAI Chat')
        return AzureChatOpenAI(
            azure_deployment=os.getenv("OPENAI_CHAT_DEPLOYMENT"), 
            api_version=os.getenv("OPENAI_CHAT_API_VERSION"),
            temperature=float(os.getenv("OPENAI_CHAT_TEMPERATURE")),
            max_tokens=int(os.getenv("OPENAI_CHAT_MAX_TOKENS")),
            timeout=int(os.getenv("OPENAI_CHAT_TIMEOUT")),
            max_retries=int(os.getenv("OPENAI_CHAT_MAX_RETRIES"))
        )