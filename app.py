import streamlit as st
import snowflake.connector
from cryptography.hazmat.primitives import serialization

st.title("Cosense App 🚀")

try:
    private_key = serialization.load_pem_private_key(
        st.secrets["snowflake"]["private_key"].encode(),
        password=None
    )

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
```

## 4. requirements.txt 에 추가
```
cryptography
