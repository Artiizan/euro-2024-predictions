import Common
import streamlit as st

Common.print_menu({
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
})

conn = Common.get_connection()
results = conn.read(worksheet="Results")
st.dataframe(results)
