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
        "tournament_winner"
    )).data)
    member_standings = pd.merge(members_data, standings_data, left_on='id', right_on='member_id')
    return member_standings

def update_standings(stage, home, away, home_goals, away_goals, home_penalties=None, away_penalties=None, next_game=None):
    # Fetch data from the database
    matches = pd.DataFrame(execute_query(client.table("matches").select("number", "home", "home_goals", "away", "away_goals", "stage", "next_game").order("number")).data)
    predictions = pd.DataFrame(execute_query(client.table("predictions").select("member_id", "match_number", "home_team_prediction", "home_goals_prediction", "away_team_prediction", "away_goals_prediction")).data)

    # Join the data
    df = pd.merge(matches, predictions, left_on='number', right_on='match_number')
    df = df[["member_id", "match_number", "home_goals", "away_goals", "home_goals_prediction", "away_goals_prediction", "stage", "home", "home_team_prediction", "away", "away_team_prediction"]]

    # Initialize the standings DataFrame
    standings = pd.DataFrame(columns=['member_id', 'group_home_goals', 'group_away_goals', 'group_result', 'group_perfect_prediction', 'tournament_winner', 'total'])

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

    ### Calculate and store Knockout Points

    if stage != 'Group' and stage != 'Final':
        # Update the team names for the Quarter finals
        if home_goals > away_goals:
            winner = home
        if home_goals < away_goals:
            winner = away
        if home_goals == away_goals:
            if home_penalties > away_penalties:
                winner = home
            if home_penalties < away_penalties:
                winner = away
    
        # Get the match to update
        next_match_number = next_game.split("-")[0]

        # Update the next match with the winner
        if next_game.split("-")[1] == 'home':
            execute_query(client.table("matches").update(next_match_number, {"home": winner}))
        if next_game.split("-")[1] == 'away':
            execute_query(client.table("matches").update(next_match_number, {"away": winner}))

    if stage == 'Final':
        # Workout the match winner
        final_match = df[df['stage'] == 'Finals']
        final_match['winner'] = final_match.apply(lambda x: x['home'] if x['home_goals'] > x['away_goals'] else x['away'], axis=1)

        # Get the members
        members = pd.DataFrame(execute_query(client.table("members").select("id", "winning_team")).data)
        update_standings_array = [
            {
                'member_id': row['id'],
                'tournament_winner': 1 if row['winning_team'] == final_match['winner'].values[0] else 0
            }
            for index, row in members.iterrows()
        ]
        execute_query(client.table("standings").upsert(update_standings_array))

@st.cache_data(ttl=300)
def get_knockout_round_points():
    # Prepare DataFrames
    matches = pd.DataFrame(execute_query(client.table("matches").select("number", "home", "away", "stage").order("number")).data)
    predictions = pd.DataFrame(execute_query(client.table("predictions").select("member_id", "match_number", "home_team_prediction", "away_team_prediction")).data)

    # Join predictions with matches to get the stage information
    predictions_with_stage = pd.merge(predictions, matches, left_on='match_number', right_on='number', how='left')

    # Define Stage Points
    stage_points = {
        'Round of 16': 1,
        'Quarter finals': 1,
        'Semi finals': 1,
        'Finals': 1
    }

    points_per_member = []

    for stage, points_per_team in stage_points.items():
        actual_teams_stage = set(matches[matches['stage'] == stage]['home'].tolist() + matches[matches['stage'] == stage]['away'].tolist())
        stage_predictions = predictions_with_stage[predictions_with_stage['stage'] == stage]
        
        for member_id, group in stage_predictions.groupby('member_id'):
            predicted_teams = set(group['home_team_prediction'].tolist() + group['away_team_prediction'].tolist())
            correct_predictions = len(predicted_teams & actual_teams_stage)
            points_per_member.append({'member_id': member_id, 'stage': stage, 'points': correct_predictions})
    
    # Convert to DataFrame
    df_points = pd.DataFrame(points_per_member)

    # Pivot Table to show points per stage for each member
    pivot_df = df_points.pivot_table(index='member_id', columns='stage', values='points', fill_value=0).reset_index()

    # Adjust namings and data types
    pivot_df['round_of_16'] = pivot_df['Round of 16'].astype('Int64')
    pivot_df['quarter_finals'] = pivot_df['Quarter finals'].astype('Int64')
    pivot_df['semi_finals'] = pivot_df['Semi finals'].astype('Int64')
    pivot_df['finals'] = pivot_df['Finals'].astype('Int64')

    return pivot_df

@st.cache_data(ttl=300)
def get_standings_totals(member_standings):
    # Calculate group points
    member_standings['group_goals'] = member_standings['group_home_goals'] + member_standings['group_away_goals']
    member_standings['total'] = member_standings['group_goals'] + (member_standings['group_result'] * 3) + (member_standings['group_perfect_prediction'] * 3)
    
    # Calculate total with knockout points
    member_standings['tournament_winner'] = member_standings['tournament_winner'].fillna(0)
    member_standings['total'] = member_standings['total'] + (member_standings['round_of_16'] * 3) + (member_standings['quarter_finals'] * 4) + (member_standings['semi_finals'] * 6) + (member_standings['finals'] * 8) + (member_standings['tournament_winner'] * 20)

    member_standings = member_standings.sort_values(by='total', ascending=False).reset_index(drop=True)
    member_standings.insert(0, 'position', range(1, 1 + len(member_standings)))
    member_standings['group_perfect'] = member_standings['group_perfect_prediction']
    member_standings = member_standings[['position', 'name', 'group_goals', 'group_result', 'group_perfect', 'round_of_16', 'quarter_finals', 'semi_finals', 'finals', 'total']]

    return member_standings