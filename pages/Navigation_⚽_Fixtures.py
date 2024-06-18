import Common
import streamlit as st
from st_supabase_connection import execute_query

Common.print_menu()

client = Common.get_database_client()
data = execute_query(client.table("matches").select(
    "number",
    "home",
    "away",
    "home_goals",
    "away_goals",
    "stage",
    "group",
    "date",
    "time"
).order("number")).data

st.header("⚽ Fixtures", divider="grey")
st.dataframe(data)
