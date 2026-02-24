import re
import config

# Keywords that strongly indicate a structured data query
_SQL_KEYWORDS = {
    "list", "top", "average", "count", "show",
    "highest", "lowest", "how many", "total", "sum",
}

# Analytical question starters that indicate a knowledge/strategy query even
# if they contain an incidental SQL keyword (e.g. "why is churn *highest*?")
_RAG_OVERRIDE_PATTERNS = (
    r"\bwhy\b", r"\bwhat causes\b", r"\bwhat is the reason\b",
    r"\bexplain\b", r"\bhow does\b", r"\bwhat drives\b",
    r"\binsight\b", r"\bstrateg", r"\brecommend",
)


def _rule_based(query: str) -> str | None:
    lower = query.lower()
    for pattern in _RAG_OVERRIDE_PATTERNS:
        if re.search(pattern, lower):
            return "rag"
    for keyword in _SQL_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", lower):
            return "sql"
    return None


def _llm_classify(query: str) -> str:
    from google import genai
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    classification_prompt = (
        "You are a query router for a telecom analytics assistant.\n"
        "Classify the following user query as either 'sql' (structured data lookup) "
        "or 'rag' (knowledge / strategy question).\n"
        "Respond with ONLY one word: sql or rag.\n\n"
        f"Query: {query}"
    )
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=classification_prompt,
        )
        label = response.text.strip().lower()
        return "sql" if "sql" in label else "rag"
    except Exception:
        return "rag"


def route(query: str) -> str:
    decision = _rule_based(query)
    if decision:
        return decision
    # Ambiguous — use LLM classification
    return _llm_classify(query)
