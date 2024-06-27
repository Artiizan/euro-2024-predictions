import Common
import Database
import pandas as pd
import streamlit as st
from datetime import date
from st_supabase_connection import execute_query

st.set_page_config(
    page_title="Euro 2024 - Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
if not Common.check_password(): st.stop()
Common.print_menu()
client = Common.get_database_client()
today = date.today()

####################################################################################################
# Database
####################################################################################################

@st.cache_data(ttl=300)
def get_todays_matches():
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
    return today_df

####################################################################################################
# Page content
####################################################################################################

st.title("2024 European Championships ⚽")
st.subheader("Welcome to the Williams Euro predictions tracker", divider="rainbow")

# Today's matches
st.subheader(":calendar: Today's Matches", divider="grey")

today_df = get_todays_matches()
if today_df.empty:
    st.markdown("<h3 style='text-align: center;'><em>There are no matches scheduled for today</em> 😢</h3>", unsafe_allow_html=True)
else:
    today_df['home_goals'] = today_df['home_goals'].astype('Int64')
    today_df['away_goals'] = today_df['away_goals'].astype('Int64')
    today_df['score'] = today_df.apply(lambda x: None if pd.isna(x['home_goals']) else str(x['home_goals']) + " : " + str(x['away_goals']), axis=1)
    today_df['date'] = pd.to_datetime(today_df['date']).dt.strftime('%d %B')
    today_df['uk_time'] = pd.to_datetime(today_df['time'], format="mixed").dt.strftime('%H:%M')
    today_df['stage'] = today_df.apply(lambda x: x['stage'] if pd.isna(x['group']) else f"{x['stage']} {x['group']}", axis=1)
    st.dataframe(today_df, use_container_width=True, hide_index=True, column_order=['date', 'uk_time', 'home', 'score', 'away', 'stage', 'stadium'])

# Standings
st.subheader(":trophy: Prediction Standings", divider="blue")
standings = Database.get_standings()

# Get knockout round points
knockout_round_points = Database.get_knockout_round_points()
standings = standings.merge(knockout_round_points, on='member_id', how='left')

# Get the total points
member_standings = Database.get_standings_totals(standings)

### Styling
# Highlight the highest score in each column in green
def highlight_max(s):
    if pd.isna(s).all() or s.max() == 0:
        return ['' for _ in s]
    is_max = s == s.max()
    return ['background-color: green' if v else '' for v in is_max]

# Add medals
member_standings.loc[member_standings['position'] == 1, 'position'] = '🥇'
member_standings.loc[member_standings['position'] == 2, 'position'] = '🥈'
member_standings.loc[member_standings['position'] == 3, 'position'] = '🥉'

# Only show the knockout round columns if the tournament has reached that stage
if today < date(2024, 6, 30):
    # Hide the quarter finals, semifinals and finals columns if the tournament has not reached that stage
    member_standings = member_standings[[ 'position', 'name', 'group_goals', 'group_result', 'group_perfect', 'round_of_16', 'total' ]]
    member_standings = member_standings.style.apply(highlight_max, subset=['group_goals', 'group_result', 'group_perfect', 'round_of_16'])
elif today < date(2024, 7, 3):
    # Hide the semifinals and finals columns if the tournament has not reached that stage
    member_standings = member_standings[[ 'position', 'name', 'group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals', 'total' ]]
    member_standings = member_standings.style.apply(highlight_max, subset=['group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals'])
elif today < date(2024, 7, 6):
    # Hide the finals column if the tournament has not reached that stage
    member_standings = member_standings[[ 'position', 'name', 'group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals', 'semi_finals', 'total' ]]
    member_standings = member_standings.style.apply(highlight_max, subset=['group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals', 'semi_finals'])
else:
    # Show all columns
    member_standings = member_standings.style.apply(highlight_max, subset=['group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals', 'semi_finals', 'finals', 'total'])

st.dataframe(
    member_standings,
    height=702,
    use_container_width=True, 
    hide_index=True,
)
