import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from tools.router import route
from tools.sql_tool import run_sql, pick_sql_query
from rag.retriever import retrieve
from llm.prompt_template import build_prompt
from llm.gemini_client import generate

st.set_page_config(
    page_title="Telecom  Copilot",
    page_icon="\U0001f4e1",
    layout="centered",
)

st.title("Telecom  Copilot")
st.caption("Retention Intelligence Assistant powered by Gemini \u00b7 RAG \u00b7 SQL")
st.divider()

user_query = st.text_input(
    label="Enter your  question:",
    placeholder="e.g. What are the top 10 highest churn risk subscribers?",
)

generate_btn = st.button("Generate Insight", type="primary")

if generate_btn:
    if not user_query.strip():
        st.warning("Please enter a question before generating an insight.")
    else:
        with st.spinner("Analysing query and generating insight..."):
            intent = route(user_query)

            sql_result = ""
            context = ""
            raw_docs = ""
            raw_sql = ""

            if intent == "sql":
                sql_query = pick_sql_query(user_query)
                sql_result = run_sql(sql_query)
                raw_sql = f"**Query:**\n```sql\n{sql_query}\n```\n\n**Result:**\n```\n{sql_result}\n```"
            else:
                context = retrieve(user_query)
                raw_docs = context

            prompt = build_prompt(
                query=user_query,
                context=context,
                sql_result=sql_result,
            )

            response = generate(prompt)

        st.divider()
        st.subheader("Insight")
        st.markdown(response)

        with st.expander("Retrieved Knowledge Documents", expanded=False):
            if raw_docs:
                st.markdown(raw_docs)
            else:
                st.info("No documents retrieved for this query.")

        with st.expander("SQL Results", expanded=False):
            if raw_sql:
                st.markdown(raw_sql)
            else:
                st.info("No SQL query was executed for this question.")

        st.caption(f"Routing decision: **{intent.upper()}**")
