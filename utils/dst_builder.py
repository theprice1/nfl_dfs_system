import pandas as pd
import nflreadpy as nfl
import os

def build_dst_projections():
    print("Downloading 2023 schedule data for Points Allowed...")
    # 1. Load schedules to calculate points allowed per game
    schedules = nfl.load_schedules([2023]).to_pandas()
    
    # Filter for regular season only
    schedules = schedules[schedules['game_type'] == 'REG']
    
    # Extract points allowed by looking at the score of the opposing team
    home_def = schedules[['home_team', 'away_score']].rename(columns={'home_team': 'Team', 'away_score': 'pts_allowed'})
    away_def = schedules[['away_team', 'home_score']].rename(columns={'away_team': 'Team', 'home_score': 'pts_allowed'})
    
    # Combine to get a master list of every game played by every defense
    defense_games = pd.concat([home_def, away_def])
    
    # 2. Apply FanTeam's Points Allowed Bracket
    def calc_pts_allowed_score(pts):
        if pts == 0: return 10
        elif 1 <= pts <= 6: return 7
        elif 7 <= pts <= 13: return 4
        elif 14 <= pts <= 20: return 1
        elif 21 <= pts <= 27: return 0
        elif 28 <= pts <= 34: return -1
        else: return -4
        
    defense_games['bracket_points'] = defense_games['pts_allowed'].apply(calc_pts_allowed_score)
    
    # Sum up the bracket points for the season for each team
    dst_scoring = defense_games.groupby('Team')['bracket_points'].sum().reset_index()

    print("Downloading player stats for Sacks and Interceptions...")
    # 3. Load player stats to calculate Sacks and INTs forced
    offense = nfl.load_player_stats([2023]).to_pandas()
    
    # Group by the OPPONENT_TEAM to see what mistakes the defense forced
    defense_turnovers = offense.groupby('opponent_team').agg({
        'sacks_suffered': 'sum',
        'passing_interceptions': 'sum'
    }).reset_index()
    defense_turnovers = defense_turnovers.rename(columns={'opponent_team': 'Team'})
    
    # Apply FanTeam scoring (Sacks = 1pt, INTs = 2pts)
    defense_turnovers['turnover_points'] = (defense_turnovers['sacks_suffered'] * 1) + (defense_turnovers['passing_interceptions'] * 2)
    
    # 4. Merge the brackets and the turnovers together
    dst_final = pd.merge(dst_scoring, defense_turnovers, on='Team')
    dst_final['Projected_Points'] = dst_final['bracket_points'] + dst_final['turnover_points']
    
    # 5. Format to perfectly match our existing optimizer CSV
    dst_final['Player'] = dst_final['Team'] + " DST"
    dst_final['Position'] = 'DST'
    
    dst_export = dst_final[['Player', 'Position', 'Team', 'Projected_Points']].copy()
    dst_export['Projected_Points'] = dst_export['Projected_Points'].round(2)
    
    # 6. Append this directly to the bottom of our existing baseline_projections.csv
    output_path = os.path.join("data", "uploads", "baseline_projections.csv")
    
    if os.path.exists(output_path):
        existing_proj = pd.read_csv(output_path)
        # Remove old DSTs if we run the script twice so we don't duplicate
        existing_proj = existing_proj[existing_proj['Position'] != 'DST']
        final_csv = pd.concat([existing_proj, dst_export]).sort_values(by='Projected_Points', ascending=False)
    else:
        final_csv = dst_export
        
    final_csv.to_csv(output_path, index=False)
    
    print(f"Success! Appended 32 DST projections to {output_path}")

if __name__ == "__main__":
    build_dst_projections()