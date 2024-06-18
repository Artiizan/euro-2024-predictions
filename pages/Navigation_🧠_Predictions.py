import Common
import streamlit as st
from st_supabase_connection import execute_query
import pandas as pd

st.set_page_config(
    page_title="Euro 2024 - Predictions",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)
Common.print_menu()
client = Common.get_database_client()

# Fetch the matches to use later
matches = execute_query(client.table("matches").select(
    "number",
    "home",
    "home_goals",
    "away",
    "away_goals",
    "group",
    "stage"
).order("number")).data

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

# Set column data types
df['home_goals'] = df['home_goals'].astype('Int64')
df['away_goals'] = df['away_goals'].astype('Int64')
df['actual_score'] = df.apply(lambda x: None if pd.isna(x['home_goals']) else str(x['home_goals']) + " : " + str(x['away_goals']), axis=1)
df['home_goals_prediction'] = df['home_goals_prediction'].astype('Int64')
df['away_goals_prediction'] = df['away_goals_prediction'].astype('Int64')
df['predicted_score'] = df.apply(lambda x: None if pd.isna(x['home_goals_prediction']) else str(x['home_goals_prediction']) + " : " + str(x['away_goals_prediction']), axis=1)
df['stage'] = df.apply(lambda x: x['stage'] if pd.isna(x['group']) else f"{x['stage']} {x['group']}", axis=1)

# Styling the dataframe
def style_row(row):
    # Default styles
    styles = [''] * len(row)

    # If the game hasn't been played yet
    if pd.isna(row['home_goals']):
        return styles

    # If the perfect score is predicted
    if row['home_goals'] == row['home_goals_prediction'] and row['away_goals'] == row['away_goals_prediction']:
        return ['background-color: orange'] * len(row)

    # If the correct winner is predicted
    if (row['home_goals'] > row['away_goals'] and row['home_goals_prediction'] > row['away_goals_prediction']) or \
       (row['home_goals'] < row['away_goals'] and row['home_goals_prediction'] < row['away_goals_prediction']):
        styles[0] = 'background-color: green'  # number
        if row['home_goals'] == row['home_goals_prediction']:
            styles[1] = 'background-color: green'  # home
            styles[2] = 'background-color: green'  # predicted_score
        if row['away_goals'] == row['away_goals_prediction']:
            styles[3] = 'background-color: green'  # away
            styles[2] = 'background-color: green'  # predicted_score
    else:
        styles[0] = 'background-color: red'  # number
        if row['home_goals'] == row['home_goals_prediction']:
            styles[1] = 'background-color: green'  # home
            styles[2] = 'background-color: green'  # predicted_score
        if row['away_goals'] == row['away_goals_prediction']:
            styles[3] = 'background-color: green'  # away
            styles[2] = 'background-color: green'  # predicted_score

    return styles

styled_df = df.style.apply(style_row, axis=1)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=800, 
    hide_index=True,
    column_order=['number', 'home', 'predicted_score', 'away', 'actual_score']
)

# Add a section at the bottom of the webpage to explain the colorings and rules
st.markdown("""
### Key
- <span style='color:orange'>**Orange row**</span>: The perfect score was predicted.
- <span style='color:green'>**Green number**</span>: The correct winner was predicted.
- <span style='color:green'>**Green home or away**</span>: The correct number of home or away goals was predicted.
- <span style='color:red'>**Red number**</span>: The predicted winner was wrong.
""", unsafe_allow_html=True)
