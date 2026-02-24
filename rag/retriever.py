from rag.knowledge_loader import load_documents
from rag.vector_store import build_index
import config

_documents = load_documents()
_index = build_index(_documents)


def retrieve(query: str) -> str:
    results = _index.similarity_search(query, k=config.RAG_TOP_K)

    if not results:
        return "No relevant knowledge found."

    snippets = []
    for doc in results:
        title = doc.metadata.get("title", "Knowledge Entry")
        snippets.append(f"**{title}**\n{doc.page_content}")

    return "\n\n---\n\n".join(snippets)
