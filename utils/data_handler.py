import pandas as pd
import os

def prepare_master_dataframe():
    print("Loading FanTeam rules and salaries...")
    
    # Paths
    fanteam_path = os.path.join("data", "uploads", "1136503_players_20260826031647.csv")
    projections_path = os.path.join("data", "uploads", "baseline_projections.csv")
    
    if not os.path.exists(fanteam_path):
        print(f"Error: Could not find {fanteam_path}")
        return
        
    # 1. Load Data
    ft_df = pd.read_csv(fanteam_path)
    proj_df = pd.read_csv(projections_path)
    
    # 2. Clean FanTeam Names to match our projections
    # Fill missing first names (like DSTs), combine, and strip whitespace
    ft_df['Full_Name'] = ft_df['FName'].fillna('') + " " + ft_df['Name']
    ft_df['Full_Name'] = ft_df['Full_Name'].str.strip()
    
    # Map FanTeam's long positions to our short codes
    pos_map = {
        'quarterback': 'QB',
        'running_back': 'RB',
        'wide_receiver': 'WR',
        'tight_end': 'TE',
        'defense_special': 'DST'
    }
    ft_df['Pos_Short'] = ft_df['Position'].map(pos_map)
    
    # Rename defenses to match our "TEAM DST" projection format
    ft_df.loc[ft_df['Pos_Short'] == 'DST', 'Full_Name'] = ft_df['Club'] + " DST"
    
    # 3. Merge!
    # Left merge so we keep every FanTeam player, even if they have no 2023 stats
    master_df = pd.merge(
        ft_df,
        proj_df[['Player', 'Projected_Points']],
        left_on='Full_Name',
        right_on='Player',
        how='left'
    )
    
    # Any rookies or backups without 2023 stats get 0 projected points for now
    master_df['Projected_Points'] = master_df['Projected_Points'].fillna(0)
    
    # 4. Clean up columns for the PuLP engine
    final_df = master_df[['PlayerID', 'Full_Name', 'Pos_Short', 'Club', 'Price', 'Projected_Points']].copy()
    final_df.columns = ['ID', 'Player', 'Position', 'Team', 'Price', 'Projected_Points']
    
    # Sort by highest projected points
    final_df = final_df.sort_values(by='Projected_Points', ascending=False)
    
    # 5. Save the unified master list
    output_path = os.path.join("data", "outputs", "master_player_list.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    
    print(f"Success! Merged {len(final_df)} FanTeam players with projections.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    prepare_master_dataframe()