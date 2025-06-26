class BaseVectorStore:
    def load_index(self, index_path, embeddings,  db_config=None):
        raise NotImplementedError("Load method not implemented.")

    def as_retriever(self):
        raise NotImplementedError("as_retriever method not implemented.")

    @classmethod
    def from_documents(cls, documents, embeddings,  db_config):
        raise NotImplementedError("from_documents method not implemented.")

    def save_index(self, index_path):
        raise NotImplementedError("save_local method not implemented.")
    
    def similarity_search_with_score(self, query, k=4):
        raise NotImplementedError("similarity_search_with_score method not implemented.")