import Common
import pandas as pd
import streamlit as st
from st_supabase_connection import execute_query

client = Common.get_database_client()

####################################################################################################
# Standings
####################################################################################################

@st.cache_data(ttl=300)
def get_standings():
    members_data = pd.DataFrame(execute_query(client.table("members").select("id", "name")).data)
    standings_data = pd.DataFrame(execute_query(client.table("standings").select(
        "member_id",
        "group_home_goals",
        "group_away_goals",
        "group_result",
        "group_perfect_prediction",
    )).data)
    member_standings = pd.merge(members_data, standings_data, left_on='id', right_on='member_id')

    # Calculate total points
    member_standings['group_goals'] = member_standings['group_home_goals'] + member_standings['group_away_goals']
    member_standings['total'] = member_standings['group_goals'] + (member_standings['group_result'] * 3) + (member_standings['group_perfect_prediction'] * 3)
    
    member_standings = member_standings.sort_values(by='total', ascending=False).reset_index(drop=True)
    member_standings.insert(0, 'position', range(1, 1 + len(member_standings)))
    member_standings['group_perfect'] = member_standings['group_perfect_prediction']
    member_standings = member_standings[['position', 'name', 'group_goals', 'group_result', 'group_perfect', 'total']]

    return member_standings

def update_standings(stage):
    # Fetch data from the database
    matches = pd.DataFrame(execute_query(client.table("matches").select("number", "home", "home_goals", "away", "away_goals", "stage").order("number")).data)
    predictions = pd.DataFrame(execute_query(client.table("predictions").select("member_id", "match_number", "home_team_prediction", "home_goals_prediction", "away_team_prediction", "away_goals_prediction")).data)

    # Join the data to get a row with the following columns
    df = pd.merge(matches, predictions, left_on='number', right_on='match_number')
    df = df[["member_id", "match_number", "home_goals", "away_goals", "home_goals_prediction", "away_goals_prediction", "stage"]]

    # Initialize the standings DataFrame
    standings = pd.DataFrame(columns=['member_id', 'group_home_goals', 'group_away_goals', 'group_result', 'group_perfect_prediction', 'total'])

    ### Calculate and store Group Points
    if stage == 'Group':
        group_matches = df[df['stage'] == 'Group']
        for _, row in group_matches.iterrows():
            member = row['member_id']
            # Initialize the member's row in standings if it doesn't exist
            if member not in standings['member_id'].values:
                standings = standings._append({
                    'member_id': member, 
                    'group_home_goals': 0,
                    'group_away_goals': 0,
                    'group_result': 0,
                    'group_perfect_prediction': 0,
                }, ignore_index=True)
            
            # Calculate points
            if row['home_goals'] == row['home_goals_prediction']:
                standings.loc[standings['member_id'] == member, 'group_home_goals'] += 1
            if row['away_goals'] == row['away_goals_prediction']:
                standings.loc[standings['member_id'] == member, 'group_away_goals'] += 1
            if (row['home_goals'] - row['away_goals']) * (row['home_goals_prediction'] - row['away_goals_prediction']) > 0:
                standings.loc[standings['member_id'] == member, 'group_result'] += 1
            if (row['home_goals'] == row['away_goals'] and row['home_goals_prediction'] == row['away_goals_prediction']):
                standings.loc[standings['member_id'] == member, 'group_result'] += 1
            if row['home_goals'] == row['home_goals_prediction'] and row['away_goals'] == row['away_goals_prediction']:
                standings.loc[standings['member_id'] == member, 'group_perfect_prediction'] += 1
        
        standings['group_total'] = standings['group_home_goals'] + standings['group_away_goals'] + (standings['group_result'] * 3) + (standings['group_perfect_prediction'] *3)
        update_standings_array = [
            {
                'member_id': row['member_id'],
                'group_home_goals': row['group_home_goals'],
                'group_away_goals': row['group_away_goals'],
                'group_result': row['group_result'],
                'group_perfect_prediction': row['group_perfect_prediction']
            }
            for index, row in standings.iterrows()
        ]
        execute_query(client.table("standings").upsert(update_standings_array))
