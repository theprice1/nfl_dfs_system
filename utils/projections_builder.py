import pandas as pd
import nflreadpy as nfl
import os

def build_baseline_projections():
    print("Downloading historical NFL data... (This may take a minute)")
    
    # 1. Fetch weekly player stats using the modern nflreadpy library
    df_2023 = nfl.load_player_stats([2023]).to_pandas()
    
    # 2. Filter for only the offensive positions we care about
    valid_positions = ['QB', 'RB', 'WR', 'TE']
    df = df_2023[df_2023['position'].isin(valid_positions)]
    
    # 3. Group the weekly data into full-season totals for each player
    season_totals = df.groupby(['player_display_name', 'position', 'team']).agg({
        'passing_yards': 'sum',
        'passing_tds': 'sum',
        'passing_interceptions': 'sum', 
        'rushing_yards': 'sum',
        'rushing_tds': 'sum',
        'receptions': 'sum',
        'receiving_yards': 'sum',
        'receiving_tds': 'sum'
    }).reset_index()

    print("Applying FanTeam scoring rules...")

    # 4. Apply your exact FanTeam scoring multipliers to the raw stats
    season_totals['fanteam_points'] = (
        (season_totals['passing_yards'] * 0.04) +
        (season_totals['passing_tds'] * 4) +
        (season_totals['passing_interceptions'] * -2) +
        (season_totals['rushing_yards'] * 0.1) +
        (season_totals['rushing_tds'] * 6) +
        (season_totals['receptions'] * 1) +
        (season_totals['receiving_yards'] * 0.1) +
        (season_totals['receiving_tds'] * 6)
    )
    
    # 5. Clean up the dataframe for the optimizer
    final_projections = season_totals[[
        'player_display_name', 
        'position', 
        'team', 
        'fanteam_points'
    ]].copy()
    
    final_projections.columns = ['Player', 'Position', 'Team', 'Projected_Points']
    
    # Round the points to 2 decimal places and sort by highest points
    final_projections['Projected_Points'] = final_projections['Projected_Points'].round(2)
    final_projections = final_projections.sort_values(by='Projected_Points', ascending=False)
    
    # 6. Save the CSV directly into our uploads directory
    output_path = os.path.join("data", "uploads", "baseline_projections.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_projections.to_csv(output_path, index=False)
    
    print(f"Success! Saved {len(final_projections)} players to {output_path}")

if __name__ == "__main__":
    build_baseline_projections()