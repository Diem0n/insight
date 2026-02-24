import re
import sqlite3
import pandas as pd
import config

_BLOCKED_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "replace")

_SQL_QUERY_MAP = {
    "average": "SELECT segment_label, ROUND(AVG(churn_probability), 4) AS avg_churn_prob FROM subscribers GROUP BY segment_label ORDER BY avg_churn_prob DESC;",
    "top":     "SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type FROM subscribers ORDER BY churn_probability DESC LIMIT {n};",
    "highest": "SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type FROM subscribers ORDER BY churn_probability DESC LIMIT {n};",
    "lowest":  "SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type FROM subscribers ORDER BY churn_probability ASC LIMIT {n};",
    "list":    "SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type, tenure FROM subscribers ORDER BY churn_probability DESC LIMIT {n};",
    "show":    "SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type, tenure FROM subscribers LIMIT {n};",
    "count":   "SELECT contract_type, COUNT(*) AS subscriber_count FROM subscribers GROUP BY contract_type ORDER BY subscriber_count DESC;",
    "how many":"SELECT contract_type, COUNT(*) AS subscriber_count FROM subscribers GROUP BY contract_type ORDER BY subscriber_count DESC;",
    "total":   "SELECT segment_label, COUNT(*) AS total_subscribers FROM subscribers GROUP BY segment_label ORDER BY total_subscribers DESC;",
    "sum":     "SELECT segment_label, ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue FROM subscribers GROUP BY segment_label ORDER BY total_monthly_revenue DESC;",
}


def extract_limit(query: str, default: int = 10) -> int:
    match = re.search(r"\b(?:top|list|show|lowest|highest)\s+(\d+)\b", query.lower())
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s+(?:highest|lowest|subscriber|record)", query.lower())
    if match:
        return int(match.group(1))
    return default


def pick_sql_query(query: str) -> str:
    lower = query.lower()
    n = extract_limit(query)
    for keyword, sql in _SQL_QUERY_MAP.items():
        if keyword in lower:
            return sql.format(n=n) if "{n}" in sql else sql
    return f"SELECT subscriber_id, segment_label, churn_probability, monthly_charges, contract_type, tenure FROM subscribers ORDER BY churn_probability DESC LIMIT {n};"


def _is_safe(query: str) -> bool:
    normalized = query.strip().lower()
    if not normalized.startswith("select"):
        return False
    for keyword in _BLOCKED_KEYWORDS:
        if keyword in normalized:
            return False
    return True


def run_sql(query: str) -> str:
    if not _is_safe(query):
        return "Query blocked: only SELECT statements are permitted."

    try:
        conn = sqlite3.connect(config.DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "Query executed successfully but returned no results."

        return df.to_string(index=False)

    except Exception as exc:
        return f"SQL execution error: {exc}"
