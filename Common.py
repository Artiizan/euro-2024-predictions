import os
import re
import logging
import streamlit as st
from pathlib import Path
from st_supabase_connection import SupabaseConnection

logo_path = os.path.join(os.path.abspath(os.getcwd()), "resources", "logo.png")

EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|"
    "[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|"
    "[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|"
    "[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|"
    "[\U0001FA70-\U0001FAFF]|[\U00002702-\U000027B0]|"
    "[\U000024C2-\U0001F251]|[\U0001f926-\U0001f937]|"
    "[\U0001F1E0-\U0001F1FF]+",
    flags=re.UNICODE,
)

def print_menu():
    """
    Prints the logo at the top of the Streamlit sidebar.
    """

    # set the logging level for the PIL logger,
    # as it's quite noisy with unuseful information
    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    # draw the app header
    if os.path.exists(logo_path):
        col_icon, col_title, _ = st.sidebar.columns([1.4, 2, 0.6])
        image = Path(logo_path).read_bytes()
        col_icon.markdown("")
        col_icon.image(image, use_column_width=True)
        col_title.header('Euro 2024 Predictions')
    else:
        col_title, _ = st.sidebar.columns([2, 0.8])
        st.sidebar.header('Euro 2024 Predictions')

    # draw available pages
    with st.sidebar:
        st.page_link("streamlit_app.py", label="Dashboard", icon="🏠")
        st.page_link("pages/Predictions.py", label="Predictions", icon="🧠")
        st.page_link("pages/Fixtures.py", label="Fixtures & Results", icon="⚽")

        # check if the user is an admin
        if "is_admin" in st.session_state and st.session_state.is_admin:
            st.markdown("#### Administration")
            st.page_link("pages/Admin_Update_Scores.py", label="Update match scores", icon="🧮")


def get_first_emoji(text):
    # Find the first emoji in the text
    match = re.search(EMOJI_PATTERN, text)

    if match:
        return match.group()
    else:
        return None

import hmac
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            st.session_state["is_admin"] = False
            del st.session_state["password"]  # Don't store the password.
        elif hmac.compare_digest(st.session_state["password"], st.secrets["admin_password"]):
            st.session_state["password_correct"] = True
            st.session_state["is_admin"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["is_admin"] = False
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# Database
st_supabase_client = st.connection(
    name = "euro-predictions",
    type = SupabaseConnection,
    ttl = 300
)

def get_database_client():
    return st_supabase_client
