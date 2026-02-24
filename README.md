# Telecom Copilot

A production-structured retention intelligence assistant that answers commercial telecom questions using a hybrid RAG + SQL + Gemini pipeline, served via Streamlit.

---

## Architecture

```
User Query
    │
    ▼
Router (rule-based + Gemini fallback)
    │
    ├── SQL intent ──► SQL Tool (SQLite) ──► SQL results only
    │                                               │
    └── RAG intent ──► FAISS Retriever ──► Knowledge context only
                                                    │
                                               (separate paths,
                                            no cross-contamination)
                                                    │
                                                    ▼
                                           Prompt Builder
                                      (strict numeric grounding:
                                       only cite values present
                                       in provided data)
                                                    │
                                                    ▼
                                          Gemini 2.5 Flash
                                                    │
                                                    ▼
                                        ### Summary
                                        ### Data Evidence
                                        ### Strategic Recommendation
```

---

## Project Structure

```
insight/
├── app/
│   └── streamlit_app.py        # UI and query orchestration
├── data/
│   ├── telecom_knowledge.json  # 6-entry knowledge base
│   └── subscriber_sample.db    # SQLite: 80 subscribers, 4 segments
├── llm/
│   ├── gemini_client.py        # Gemini API client with retry backoff
│   └── prompt_template.py      # Enforces Summary / Data Evidence / Recommendation format
├── rag/
│   ├── knowledge_loader.py     # Loads JSON KB into LangChain Documents
│   ├── retriever.py            # FAISS similarity search (top-k)
│   └── vector_store.py         # fastembed ONNX embeddings + FAISS index
├── tools/
│   ├── router.py               # Routes query to SQL or RAG
│   └── sql_tool.py             # Safe SELECT-only SQLite executor
├── scripts/
│   ├── seed_db.py              # Seeds subscriber_sample.db
│   ├── download_model.py       # Pre-caches fastembed ONNX model
│   └── test_pipeline.py        # End-to-end pipeline tests
├── config.py                   # Centralised config + env loader
├── .env                        # GEMINI_API_KEY (not committed)
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env` in the project root:

```
GEMINI_API_KEY=your_key_here
```

Get a key at https://aistudio.google.com/app/apikey

### 3. Seed the database

```bash
python scripts/seed_db.py
```

### 4. Pre-cache the embedding model (one-time, ~90 MB ONNX download)

```bash
python scripts/download_model.py
```

### 5. Run the app

```bash
python -m streamlit run app/streamlit_app.py
```

Open http://localhost:8501

---

## How It Works

### Routing

Every query is classified as `sql` or `rag`:

| Query | Route |
|---|---|
| "List top 3 highest churn subscribers" | SQL |
| "Show average churn by segment" | SQL |
| "How many month-to-month subscribers?" | SQL |
| "Why is churn highest among early subscribers?" | RAG |
| "What strategies reduce churn?" | RAG |
| "Explain pricing sensitivity" | RAG |

Analytical phrasing (`why`, `explain`, `how does`, `recommend`, `strategy`) overrides SQL keywords. Ambiguous queries fall back to Gemini one-shot classification.

### SQL Tool

- Executes SELECT queries against `subscriber_sample.db`
- Extracts number from natural language: "top 3" → `LIMIT 3`, "list 5" → `LIMIT 5`
- Blocks all non-SELECT operations (INSERT, UPDATE, DROP, etc.)
- Returns pandas-formatted tabular output
- **RAG retrieval is skipped entirely for SQL-intent queries** — Gemini receives only the SQL result, eliminating knowledge-base bleed

#### Data Warehouse Schema Design

The `subscribers` table is modelled on a telco **subscriber fact table** as found in DWH systems (Teradata, Redshift, BigQuery):

| Column | DWH Role | Description |
|---|---|---|
| `subscriber_id` | Surrogate key | Unique subscriber identifier |
| `segment_label` | Dimension FK → `dim_segment` | Behavioral segment assigned by K-Means |
| `contract_type` | Dimension FK → `dim_contract` | Month-to-month / One year / Two year |
| `churn_probability` | Fact measure | Model-scored churn risk (0–1) |
| `monthly_charges` | Fact measure | ARPU proxy |
| `tenure` | Fact measure | Subscriber lifecycle age (months) |

Aggregation patterns in `sql_tool.py` (`GROUP BY`, `AVG()`, `COUNT()`, `ORDER BY`) are directly translatable to Teradata SQL or any ANSI-compliant DWH query layer.

### RAG Retriever

- 6 knowledge documents embedded with `fastembed` (ONNX, ~90 MB, no torch required)
- FAISS in-memory index rebuilt on startup
- Returns top-3 most relevant knowledge snippets for the query
- **SQL execution is skipped entirely for RAG-intent queries** — no cross-contamination between structured and unstructured paths

### Grounding Policy

The prompt enforces a strict numeric rule:
> *Only cite a numeric value (percentage, ratio, probability, count, dollar amount) if it appears explicitly in the provided SQL results or retrieved context. Do not estimate, infer, or recall any number from general knowledge. If a metric is not present, state: "No quantitative data available in context."*

This prevents the model from blending unrelated knowledge-base statistics into SQL responses and vice versa.

### Prompt and Output Format

Every Gemini response is strictly enforced to contain three sections:

```
### Summary
Executive overview of the answer.

### Data Evidence
- Bullet referencing retrieved knowledge snippets.
- Bullet referencing SQL results (if applicable).

### Strategic Recommendation
A concrete, telecom-aligned action.
```

---

## Knowledge Base

| Title | Key Insight |
|---|---|
| Segment Analysis Overview | 4 segments; Early High-Risk = 58% churn, 41% of revenue loss |
| Churn Model Performance | AUC-ROC 0.87; top features: contract_type, tenure, monthly_charges |
| Contract Risk Insights | Month-to-month = 3.2x higher churn; contract upgrade reduces churn by 0.31 |
| Pricing Sensitivity | >$75/month = 2.4x more likely to churn; 10-15% discount saves 34% |
| Service Stickiness | 3+ bundles = 11% churn vs 44% for single service |
| Retention Strategy | 5 programs: contract upgrade, cross-sell, proactive outreach, pricing, win-back |

---

## Subscriber Segments (SQLite)

Segments were derived using K-Means clustering with RFM-style behavioral proxies (tenure as recency, service intensity as frequency, monthly charges as monetary) — the same methodology used in the [Commercial Subscriber Risk Model](https://github.com/Diem0n/commercial_subscriber_risk_model).

| Segment | Rows | Avg Churn Probability | Churn Rate |
|---|---|---|---|
| Early High-Risk | 20 | 0.742 | 58% |
| At-Risk Mid-Value | 20 | 0.442 | 38% |
| Loyal High-Value | 20 | 0.263 | 22% |
| Stable Low-Value | 20 | 0.119 | 9% |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | >=1.32 | Web UI |
| `google-genai` | >=1.0 | Gemini 2.5 Flash API |
| `langchain-core` / `langchain-community` | >=0.2 | RAG document pipeline |
| `faiss-cpu` | >=1.8 | Vector similarity search |
| `fastembed` | >=0.7 | ONNX-based embeddings (no torch) |
| `onnxruntime` | ==1.20.0 | ONNX runtime (pinned for Windows stability) |
| `pandas` | >=2.1 | SQL result formatting |
| `python-dotenv` | >=1.0 | `.env` loading |

---

## Running Tests

```bash
python scripts/test_pipeline.py > scripts/test_output.txt 2>&1
type scripts\test_output.txt
```

Tests cover:

| Group | What is validated |
|---|---|
| A. Routing | SQL vs RAG classification for 7 query patterns |
| B. Dynamic SQL LIMIT | Number extraction ("top 3" → `LIMIT 3`) |
| C. SQL execution | Correct row counts and ordered data from SQLite |
| D. RAG retrieval | Keyword grounding against knowledge base |
| E. Prompt structure | All 3 mandatory sections present in every prompt |
| F. Gemini live | Response format + hallucination guard on % values |

---

## Dashboard

The Streamlit UI is structured as a commercial intelligence tool, not a chat interface.

**Sidebar**
- Recent Queries — last 3 queries stored in session state, clickable to re-run
- System Architecture expander — stack details (routing logic, model, embeddings, DB)

**Per-query output (in order)**

| Element | SQL mode | RAG mode |
|---|---|---|
| Mode badge | 🟩 green banner | 🟦 blue banner |
| Metadata strip | `Model · Embeddings · Vector Index · DB` (11px gray) | same |
| Metrics row | Query Type / Rows Returned / RAG Retrieved: No | Query Type / Knowledge Docs / SQL Executed: No |
| Confidence | "Structured — based on live SQL result" | "High / Moderate — grounded in N doc(s)" |
| Insight Report | `INSIGHT REPORT` header + Gemini response | same |
| Copy Raw Insight | Expander with `st.code` (native copy button) | same |
| Retrieved Docs | — | Expandable knowledge snippets |
| SQL Results | Expandable: syntax-highlighted query + interactive table (`churn_probability` as progress bar, top 5 rows) | — |
| Footer | Strict grounding policy notice | same |

---

## Sample Questions

**SQL queries:**
- "List top 3 highest churn probability subscribers."
- "Show average churn probability by segment."
- "How many subscribers are on month-to-month contracts?"
- "What is the total monthly revenue by segment?"

**RAG / strategy queries:**
- "Why is churn highest among early subscribers?"
- "What strategies should we use to retain at-risk customers?"
- "Explain the contract risk insight."
- "How does service bundling affect churn?"

