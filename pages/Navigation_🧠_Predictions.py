import Common
import streamlit as st

Common.print_menu({
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
})

conn = Common.get_connection()
predictions = conn.read(worksheet="Predictions")
st.dataframe(predictions)
