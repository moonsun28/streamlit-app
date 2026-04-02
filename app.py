import streamlit as st
import snowflake.connector
import pandas as pd

st.title("Cosense App 🚀")

conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse=st.secrets["snowflake"]["warehouse"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"]
)

query = "SELECT * FROM COSENSE_DB.ANALYTICS.DEMAND_SIGNAL LIMIT 10"
df = pd.read_sql(query, conn)

st.dataframe(df)
