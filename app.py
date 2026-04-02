import streamlit as st

conn = st.connection("snowflake")

def run_query(query):
    return conn.query(query)
