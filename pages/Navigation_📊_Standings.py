import Common
import streamlit as st

Common.print_menu({
    "layout": "wide",
    "initial_sidebar_state": "expanded",
})

conn = Common.get_connection()
standings = conn.read(worksheet="Standings")
st.dataframe(standings)
