import streamlit as st
from router import route_query

st.title("Mini Agentic RAG")

query = st.chat_input("Ask anything")

if query:
    response = route_query(query)
    st.write(response)