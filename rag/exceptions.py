class RAGException(Exception):
    pass


class EmbeddingError(RAGException):
    pass


class VectorStoreError(RAGException):
    pass
