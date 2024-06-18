import Common
import streamlit as st
import pandas as pd
from st_supabase_connection import execute_query

st.set_page_config(
    page_title="Euro 2024 - Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
Common.print_menu()
client = Common.get_database_client()

st.header("⚽ Fixtures", divider="grey")

# Fetch the matches and display them in a DataFrame
data = execute_query(client.table("matches").select(
    "number",
    "date",
    "time",
    "home",
    "home_goals",
    "away",
    "away_goals",
    "stage",
    "group",
    "stadium"
).order("number")).data
df = pd.DataFrame(data)
    
# Set column data types
df['home_goals'] = df['home_goals'].astype('Int64')
df['away_goals'] = df['away_goals'].astype('Int64')
df['score'] = df.apply(lambda x: None if pd.isna(x['home_goals']) else str(x['home_goals']) + " : " + str(x['away_goals']), axis=1)
df['date'] = pd.to_datetime(df['date']).dt.strftime('%d %B')
df['uk_time'] = pd.to_datetime(df['time'], format="mixed").dt.strftime('%H:%M')
df['stage'] = df.apply(lambda x: x['stage'] if pd.isna(x['group']) else f"{x['stage']} {x['group']}", axis=1)

# Styling the dataframe
def highlight_cells(val):
    if pd.isna(val['home_goals']) or pd.isna(val['away_goals']):
        return ['' for _ in val]
    elif val['home_goals'] > val['away_goals']:
        return ['background-color: green' if col == 'home' or col == 'score' else '' for col in val.index]
    elif val['home_goals'] < val['away_goals']:
        return ['background-color: green' if col == 'away' or col == 'score' else '' for col in val.index]
    else:
        return ['background-color: orange' if col in ['home', 'away', 'score'] else '' for col in val.index]

styled_df = df.style.apply(highlight_cells, axis=1)
st.dataframe(
    styled_df, 
    use_container_width=True, 
    height=1000, 
    hide_index=True,
    column_order=['date', 'uk_time', 'home', 'score', 'away', 'stage', 'stadium']
)

# Add a section at the bottom of the webpage to explain the colorings and rules
st.markdown("""
### Key
- <span style='color:green'>**Green**</span>: The winning team of the match.
- <span style='color:orange'>**Orange**</span>: A draw between the two teams.
""", unsafe_allow_html=True)
