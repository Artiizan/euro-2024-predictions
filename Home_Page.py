import Common
import streamlit as st
from st_supabase_connection import execute_query
from datetime import date

Common.print_menu({
    "layout": "wide",
    "page_title": "Dashboard",
    "initial_sidebar_state": "expanded",
})

client = Common.get_database_client()
today = date.today()
today_data = execute_query(client.table("matches").select("*").eq("date", today))
st.dataframe(today_data)
