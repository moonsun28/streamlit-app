import streamlit as st
import snowflake.connector
from cryptography.hazmat.primitives import serialization
import base64

st.title("Cosense App 🚀")

try:
    private_key_bytes = base64.b64decode(st.secrets["snowflake"]["private_key_base64"])
    private_key = serialization.load_der_private_key(private_key_bytes, password=None)

    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        private_key=private_key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        )
    )
    st.success("Snowflake 연결 성공")
except Exception as e:
    st.exception(e)
