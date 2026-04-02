import streamlit as st
import snowflake.connector

st.title("Cosense App 🚀")

try:
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )
    st.success("Snowflake 연결 성공")
except Exception as e:
    st.exception(e)
