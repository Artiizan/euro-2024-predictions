import Common
import streamlit as st
from st_supabase_connection import execute_query
import pandas as pd

Common.print_menu()
client = Common.get_database_client()

# Fetch the matches to use later
matches = execute_query(client.table("matches").select(
    "number",
    "home",
    "home_goals",
    "away",
    "away_goals"
)).data

st.header("🧠 Predictions", divider="grey")

# Fetch members with their IDs and names
members_data = execute_query(client.table("members").select(
    "id", "name"
).order("name")).data

# Create a dictionary mapping member names to their IDs
members_dict = {member["name"]: member["id"] for member in members_data}

# Display the selectbox with member names
selected_member_name = st.selectbox(
    "Who would you like to view predictions for?",
    list(members_dict.keys())
)

# Get the selected member's ID
selected_member_id = members_dict[selected_member_name]

# Fetch predictions for the selected member
data = execute_query(client.table("predictions").select(
    "match_number",
    "home_goals_prediction",
    "away_goals_prediction",
).eq("member_id", selected_member_id)
.order("match_number")).data

# Join the matches and data lists
joined_data = [
    {**match, **prediction}
    for match in matches
    for prediction in data
    if match["number"] == prediction["match_number"]
]
df = pd.DataFrame(joined_data)
# Filter out extra fields
df = df[["number", "home", "home_goals_prediction", "away", "away_goals_prediction", "home_goals", "away_goals"]]

st.dataframe(df, hide_index=True)
