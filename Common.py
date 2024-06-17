from pathlib import Path
import logging
import os
import re
import streamlit as st
from st_supabase_connection import SupabaseConnection

logo_path = os.path.join(os.path.abspath(os.getcwd()), "resources", "logo.png")

# Database
st_supabase_client = st.connection(
    name = "euro-predictions",
    type = SupabaseConnection,
    ttl = None,
    url = "https://ifyaynwerqyyfbghnvdk.supabase.co",
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmeWF5bndlcnF5eWZiZ2hudmRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTg2MzEzMzAsImV4cCI6MjAzNDIwNzMzMH0.NRibyWLw_3_G9JPz6lSQ1J9yC8iN0gUfJ3mI9gs6nQw"
)

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


def print_menu(page_config):
    """
    Prints the logo at the top of the Streamlit sidebar.
    """

    # set the common page properties
    st.set_page_config(**page_config)

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

        st.page_link("Home_Page.py", label="Dashboard", icon="🏠")
        path = os.path.join(os.getcwd(), "pages")

        prev_type = ""
        pages = os.listdir(path)
        ordered_pages = sorted(pages)

        for page in ordered_pages:
            page_path = os.path.join(path, page)
            page_type = page.split("_")[0]

            # Skip the page if it's an exclude page
            if page_type == "Exclude":
                continue

            page_name = page[len(page_type) + 1 : -3].replace("_", " ")
            page_icon = get_first_emoji(page_name)
            if page_icon:
                page_name = page_name[len(page_icon) + 1 :]

            if page_type != prev_type:
                st.markdown(f"#### {page_type}")
                prev_type = page_type

            st.page_link(page_path, label=page_name, icon=page_icon)


def get_first_emoji(text):
    # Find the first emoji in the text
    match = re.search(EMOJI_PATTERN, text)

    if match:
        return match.group()
    else:
        return None

def get_database_client():
    return st_supabase_client
