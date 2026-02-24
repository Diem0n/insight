import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"

EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
RAG_TOP_K: int = 3

KNOWLEDGE_PATH: str = os.path.join(os.path.dirname(__file__), "data", "telecom_knowledge.json")
DB_PATH: str = os.path.join(os.path.dirname(__file__), "data", "subscriber_sample.db")

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. Add it to your .env file."
    )

