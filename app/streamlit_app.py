import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import pandas as pd
import streamlit as st
from tools.router import route
from tools.sql_tool import run_sql, pick_sql_query
from rag.retriever import retrieve
from llm.prompt_template import build_prompt
from llm.gemini_client import generate

st.set_page_config(
    page_title="Telecom Commercial Copilot",
    page_icon="\U0001f4e1",
    layout="centered",
)

if "query_history" not in st.session_state:
    st.session_state.query_history = []

with st.sidebar:
    st.markdown("### \U0001f559 Recent Queries")
    if st.session_state.query_history:
        for q in reversed(st.session_state.query_history[-3:]):
            label = q[:52] + "\u2026" if len(q) > 52 else q
            if st.button(label, key=f"hist_{q}", use_container_width=True):
                st.session_state.pending_query = q
                st.rerun()
    else:
        st.caption("No queries yet.")
    st.divider()
    with st.expander("\u2139\ufe0f System Architecture"):
        st.markdown(
            "**Routing:** Rule-based (keyword match) \u2192 LLM fallback  \n"
            "**SQL path:** NL \u2192 SQL \u2192 SQLite (no RAG bleed)  \n"
            "**RAG path:** Query \u2192 FAISS top-3 \u2192 Gemini  \n"
            "**Grounding:** Only values in retrieved context cited  \n\n"
            "**Model:** Gemini 2.5 Flash  \n"
            "**Embeddings:** fastembed ONNX (`all-MiniLM-L6-v2`)  \n"
            "**Vector index:** FAISS in-memory  \n"
            "**Database:** SQLite \u2014 80 subscribers, 4 segments"
        )

st.title("\U0001f4e1 Telecom Commercial Copilot")
st.caption("Retention Intelligence Assistant \u2014 powered by Gemini \u00b7 RAG \u00b7 SQL")
st.divider()

default_val = st.session_state.pop("pending_query", "")
user_query = st.text_input(
    label="Enter your commercial question:",
    placeholder="e.g. What are the top 10 highest churn risk subscribers?",
    value=default_val,
)

generate_btn = st.button("Generate Insight", type="primary")

if generate_btn:
    if not user_query.strip():
        st.warning("Please enter a question before generating an insight.")
    else:
        with st.status("Processing query...", expanded=True) as status:
            st.write("\U0001f500 Routing query...")
            intent = route(user_query)

            sql_result = ""
            sql_query = ""
            sql_df = None
            context = ""
            raw_docs = ""
            docs_count = 0

            if intent == "sql":
                st.write("\U0001f5c4\ufe0f Executing SQL query...")
                sql_query = pick_sql_query(user_query)
                sql_result = run_sql(sql_query)
                try:
                    sql_df = pd.read_csv(
                        io.StringIO(sql_result), sep=r"\s{2,}", engine="python"
                    )
                except Exception:
                    sql_df = None
            else:
                st.write("\U0001f50d Retrieving knowledge documents...")
                context = retrieve(user_query)
                raw_docs = context
                docs_count = context.count("---") + 1 if context else 0

            st.write("\u2728 Generating structured insight...")
            prompt = build_prompt(query=user_query, context=context, sql_result=sql_result)
            response = generate(prompt)
            status.update(label="Analysis complete.", state="complete", expanded=False)

        if user_query not in st.session_state.query_history:
            st.session_state.query_history.append(user_query)

        st.divider()

        if intent == "sql":
            st.markdown(
                '<div style="background:#d4edda;border-left:5px solid #28a745;'
                'padding:10px 16px;border-radius:4px;margin-bottom:8px;">'
                '<b style="color:#155724;font-size:15px;">\U0001f7e9 SQL Mode</b>'
                '<span style="color:#155724;margin-left:12px;font-size:13px;">'
                'Structured data query \u2014 subscriber database</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#d1ecf1;border-left:5px solid #17a2b8;'
                'padding:10px 16px;border-radius:4px;margin-bottom:8px;">'
                '<b style="color:#0c5460;font-size:15px;">\U0001f7e6 RAG Mode</b>'
                '<span style="color:#0c5460;margin-left:12px;font-size:13px;">'
                'Knowledge retrieval query \u2014 vector index</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<p style="color:#999;font-size:11px;margin:2px 0 10px 0;">'
            'Model: Gemini 2.5 Flash&nbsp;&nbsp;|&nbsp;&nbsp;'
            'Embeddings: fastembed (ONNX)&nbsp;&nbsp;|&nbsp;&nbsp;'
            'Vector Index: FAISS&nbsp;&nbsp;|&nbsp;&nbsp;DB: SQLite</p>',
            unsafe_allow_html=True,
        )

        if intent == "sql":
            row_count = max(len(sql_result.strip().splitlines()) - 1, 0) if sql_result else 0
            col1, col2, col3 = st.columns(3)
            col1.metric("Query Type", "SQL")
            col2.metric("Rows Returned", row_count)
            col3.metric("RAG Retrieved", "No")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Query Type", "RAG")
            col2.metric("Knowledge Docs", docs_count)
            col3.metric("SQL Executed", "No")

        if intent == "rag":
            conf = "High" if docs_count >= 3 else "Moderate"
            st.caption(f"**Confidence:** {conf} \u2014 grounded in {docs_count} retrieved document(s)")
        else:
            st.caption("**Confidence:** Structured \u2014 based on live SQL result")

        st.divider()

        st.markdown(
            '<p style="font-size:13px;color:#888;letter-spacing:1px;margin-bottom:2px;">'
            'INSIGHT REPORT</p><hr style="margin-top:0;">',
            unsafe_allow_html=True,
        )
        st.markdown(response)

        with st.expander("\U0001f4cb Copy Raw Insight", expanded=False):
            st.code(response, language=None)

        st.divider()

        with st.expander("Retrieved Knowledge Documents", expanded=False):
            if raw_docs:
                st.markdown(raw_docs)
            else:
                st.info("No documents retrieved for this query.")

        with st.expander("SQL Results", expanded=False):
            if sql_query:
                st.markdown("**Query**")
                st.code(sql_query, language="sql")
                if sql_df is not None and not sql_df.empty:
                    total = len(sql_df)
                    st.markdown(f"**Result** \u2014 showing {min(5, total)} of {total} rows")
                    col_cfg = {}
                    for col in sql_df.columns:
                        if col == "churn_probability":
                            col_cfg[col] = st.column_config.ProgressColumn(
                                label="churn_probability",
                                min_value=0.0,
                                max_value=1.0,
                                format="%.4f",
                            )
                        elif sql_df[col].dtype in ["float64", "int64"]:
                            col_cfg[col] = st.column_config.NumberColumn(col, format="%.2f")
                    st.dataframe(
                        sql_df.head(5),
                        column_config=col_cfg,
                        use_container_width=True,
                    )
                elif sql_result:
                    st.code(sql_result)
            else:
                st.info("No SQL query was executed for this question.")

        st.divider()
        st.caption(
            "\U0001f512 This assistant enforces strict numeric grounding. "
            "No metrics are inferred beyond retrieved context."
        )
