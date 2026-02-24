from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
import config


class _FastEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return next(self._model.embed([text])).tolist()


def build_index(documents: list[Document]) -> FAISS:
    embeddings = _FastEmbeddings(config.EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store
