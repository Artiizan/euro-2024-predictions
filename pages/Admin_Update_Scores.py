import Common
import Database
import streamlit as st
from datetime import date
from st_supabase_connection import execute_query

st.set_page_config(
    page_title="Update match scores",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="expanded",
)
if not Common.check_password(): st.stop()
Common.print_menu()
client = Common.get_database_client()

####################################################################################################
# Database
####################################################################################################

@st.cache_data(ttl=300)
def get_played_matches():
    today = date.today()

    data = execute_query(client.table("matches").select(
        "number",
        "date",
        "home",
        "away",
        "home_goals",
        "away_goals",
        "stage",
    ).order("number")).data

    data = [match for match in data if match["date"] <= str(today)] # Filter out matches that haven't happened yet
    data = data[::-1] # Reverse the list to show the latest matches first
    matches_dict = {f"{match['date']}: {match['home']} vs {match['away']}": match["number"] for match in data}
    return matches_dict, data

####################################################################################################
# Page content
####################################################################################################

st.header("🧮 Update match scores", divider="red")

matches_dict, data = get_played_matches()
# Display the selectbox with match details
selected_match = st.selectbox(
    "Which game would you like to update the score for?",
    list(matches_dict.keys())
)
# Get the selected match
selected_match_id = matches_dict[selected_match]
selected_match_details = [match for match in data if match["number"] == selected_match_id][0]

# Display the existing scores
if selected_match_details["home_goals"] is None or selected_match_details["away_goals"] is None:
    st.markdown("<h3 style='text-align: center;'><em>No scores have been entered for this match yet.</em></h3>", unsafe_allow_html=True)
else:
    if selected_match_details['home_goals'] > selected_match_details['away_goals']:
        st.markdown(f"<h3 style='text-align: center;'><span style='color: green;'>{selected_match_details['home']} {selected_match_details['home_goals']}</span> : {selected_match_details['away_goals']} {selected_match_details['away']}</h3>", unsafe_allow_html=True)
    elif selected_match_details['home_goals'] < selected_match_details['away_goals']:
        st.markdown(f"<h3 style='text-align: center;'>{selected_match_details['home']} {selected_match_details['home_goals']} : <span style='color: green;'>{selected_match_details['away_goals']} {selected_match_details['away']}</span></h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='text-align: center;'>{selected_match_details['home']} {selected_match_details['home_goals']} : {selected_match_details['away_goals']} {selected_match_details['away']}</h3>", unsafe_allow_html=True)

# Textboxes for entering scores
col1, col2 = st.columns(2)
with col1:
    home_score = st.text_input(f"{selected_match_details['home']}", placeholder=f"{selected_match_details['home_goals']}")
with col2:
    away_score = st.text_input(f"{selected_match_details['away']} ", placeholder=f"{selected_match_details['away_goals']}")

# Button to update the scores
if st.button("Update Scores", key="update_button", help="Click to update the scores", disabled=(home_score == "" and away_score == "")):
    execute_query(client.table("matches").update({"home_goals": home_score, "away_goals": away_score}).eq("number", selected_match_id))
    if selected_match_details["stage"] == "Group":
        Database.update_standings(selected_match_details["stage"])
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Scores updated successfully! 🎉")
