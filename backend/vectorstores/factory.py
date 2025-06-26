import os
from vectorstores.cosmosdb_store import CosmosDBNoSQLStore
from vectorstores.azuresearch_store import AzureSearchStore
from config.db_cosmos_config import db_config
from config.db_cosmos_config_option_2 import db_config_option_2

def get_vectorstore(store_type, index_path, embeddings):
    store_class = get_vectorstore_class(store_type)
    use_cosmosdb = os.getenv('USE_ALTERNATIVE', 'false').lower() == 'true'
    db_config_query=db_config
    if use_cosmosdb:
        db_config_query=db_config_option_2
    return store_class.load_index(index_path, embeddings,db_config_query)

def get_vectorstore_class(store_type):
    if store_type == "CosmosDB":
        return CosmosDBNoSQLStore
    elif store_type == "AzureSearchDB":
        return AzureSearchStore
    else:
        raise ValueError(f"Unknown vectorstore type: {store_type}")