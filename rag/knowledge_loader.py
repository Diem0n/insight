import json
from langchain_core.documents import Document
import config


def load_documents() -> list[Document]:
    with open(config.KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    documents = [
        Document(
            page_content=entry["content"],
            metadata={"title": entry["title"]}
        )
        for entry in entries
    ]
    return documents
