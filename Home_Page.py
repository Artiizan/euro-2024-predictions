import Common
import streamlit as st
from st_supabase_connection import execute_query
from datetime import date

Common.print_menu()

client = Common.get_database_client()
today = date.today()
today_data = execute_query(client.table("matches").select("time", "group", "home", "away", "home_goals", "away_goals", "stadium").eq("date", today).order("time")).data
current_stage = execute_query(client.table("matches").select("stage").eq("date", today).limit(1)).data

st.title("2024 European Championships ⚽")
st.subheader(":blue[% s]" % (today), divider="grey")

st.dataframe(today_data)
