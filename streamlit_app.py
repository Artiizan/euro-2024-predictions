import hmac
import streamlit as st

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

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# After passing authentication

import Common
from st_supabase_connection import execute_query
from datetime import date
import pandas as pd

st.set_page_config(
    page_title="Euro 2024 - Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
Common.print_menu()

client = Common.get_database_client()
today = date.today()

st.title("2024 European Championships ⚽")
st.subheader("Welcome to the Williams Euro predictions tracker", divider="rainbow")

# Today's matches
st.subheader(":calendar: Today's Matches", divider="grey")

today_data = execute_query(client.table("matches").select(
    "date",
    "time",
    "stage",
    "group",
    "home", 
    "away", 
    "home_goals", 
    "away_goals", 
    "stadium"
).eq("date", today).order("time")).data

today_df = pd.DataFrame(today_data)
today_df['home_goals'] = today_df['home_goals'].astype('Int64')
today_df['away_goals'] = today_df['away_goals'].astype('Int64')
today_df['score'] = today_df.apply(lambda x: None if pd.isna(x['home_goals']) else str(x['home_goals']) + " : " + str(x['away_goals']), axis=1)
today_df['date'] = pd.to_datetime(today_df['date']).dt.strftime('%d %B')
today_df['uk_time'] = pd.to_datetime(today_df['time'], format="mixed").dt.strftime('%H:%M')
today_df['stage'] = today_df.apply(lambda x: x['stage'] if pd.isna(x['group']) else f"{x['stage']} {x['group']}", axis=1)

st.dataframe(today_df, use_container_width=True, hide_index=True, column_order=['date', 'uk_time', 'home', 'score', 'away', 'stage', 'stadium'])

# Standings
st.subheader(":trophy: Prediction Standings", divider="blue")

# Fetch data from the database
members = execute_query(client.table("members").select("id", "name").order("name")).data
matches = execute_query(client.table("matches").select("number", "home_goals", "away_goals").order("number")).data
predictions = execute_query(client.table("predictions").select("member_id", "match_number", "home_goals_prediction", "away_goals_prediction")).data

# Join the data to get a row with the following columns:
# name, match_number, home_goals, away_goals, home_goals_prediction, away_goals_prediction
df = pd.merge(
    pd.merge(
        pd.merge(
            pd.DataFrame(members), pd.DataFrame(predictions), left_on="id", right_on="member_id"
        ),
        pd.DataFrame(matches), left_on="match_number", right_on="number"
    ),
    pd.DataFrame(members), left_on="member_id", right_on="id"
)
df["name"] = df["name_x"]
df = df[["name", "match_number", "home_goals", "away_goals", "home_goals_prediction", "away_goals_prediction"]]

# Initialize the standings DataFrame
standings = pd.DataFrame(columns=['member', 'correct_home_goals', 'correct_away_goals', 'correct_result', 'perfect_prediction', 'total_points'])

# Iterate over the rows in df
for _, row in df.iterrows():
    member = row['name']
    # Initialize the member's row in standings if it doesn't exist
    if member not in standings['member'].values:
        standings = standings._append({'member': member, 'correct_home_goals': 0, 'correct_away_goals': 0, 'correct_result': 0, 'perfect_prediction': 0, 'total_points': 0}, ignore_index=True)
    
    # Calculate points
    if row['home_goals'] == row['home_goals_prediction']:
        standings.loc[standings['member'] == member, 'correct_home_goals'] += 1
    if row['away_goals'] == row['away_goals_prediction']:
        standings.loc[standings['member'] == member, 'correct_away_goals'] += 1
    if (row['home_goals'] - row['away_goals']) * (row['home_goals_prediction'] - row['away_goals_prediction']) > 0:
        standings.loc[standings['member'] == member, 'correct_result'] += 1
    if (row['home_goals'] == row['away_goals'] and row['home_goals_prediction'] == row['away_goals_prediction']):
        standings.loc[standings['member'] == member, 'correct_result'] += 1
    if row['home_goals'] == row['home_goals_prediction'] and row['away_goals'] == row['away_goals_prediction']:
        standings.loc[standings['member'] == member, 'perfect_prediction'] += 1

# Calculate total points
standings['total_points'] = standings['correct_home_goals'] + standings['correct_away_goals'] + (standings['correct_result'] * 3) + (standings['perfect_prediction'] *3)

# Sort by total points and reset index
standings = standings.sort_values(by='total_points', ascending=False).reset_index(drop=True)

# Add position
standings.insert(0, 'position', range(1, 1 + len(standings)))

# Add medals
standings.loc[standings['position'] == 1, 'position'] = '🥇'
standings.loc[standings['position'] == 2, 'position'] = '🥈'
standings.loc[standings['position'] == 3, 'position'] = '🥉'

# Highlight the highest score in each column in green
def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: green' if v else '' for v in is_max]

standings = standings.style.apply(highlight_max, subset=['correct_home_goals', 'correct_away_goals', 'correct_result', 'perfect_prediction'])

st.dataframe(
    standings,
    use_container_width=True, 
    hide_index=True,
)
