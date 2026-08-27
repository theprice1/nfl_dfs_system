import pandas as pd
import requests
import os
import time

def scrape_consensus_projections():
    print("Initializing browser spoofing to scrape 2026 projections...")
    
    # We must fake a web browser so the site doesn't block us as a bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    positions = ['qb', 'rb', 'wr', 'te']
    all_players = []

    for pos in positions:
        print(f"Scraping {pos.upper()}s...")
        url = f"https://www.fantasypros.com/nfl/projections/{pos}.php?scoring=HALF"
        
        try:
            response = requests.get(url, headers=headers)
            # Read the HTML tables from the webpage
            tables = pd.read_html(response.text)
            df = tables[0] # The main projection table is always the first one
            
            # The HTML table has a multi-level header, we flatten it
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            # Extract Player Name and Team (FantasyPros clumps them together in the first column)
            # The column is usually named something like 'Unnamed: 0_level_0_Player'
            player_col = df.columns[0]
            
            for index, row in df.iterrows():
                raw_name = str(row[player_col])
                # Typical format: "Josh Allen BUF"
                parts = raw_name.split()
                if len(parts) >= 3:
                    team = parts[-1]
                    name = " ".join(parts[:-1])
                else:
                    name = raw_name
                    team = "FA"
                
                # We initialize raw stats to 0, then try to pull them from the columns
                # Column names vary slightly by position on the site, so we use string matching
                p_yds, p_tds, p_ints = 0, 0, 0
                r_yds, r_tds = 0, 0
                rec, rec_yds, rec_tds = 0, 0, 0
                fumbles = 0
                
                for col in df.columns:
                    col_lower = col.lower()
                    if 'pass' in col_lower and 'yds' in col_lower: p_yds = float(row[col])
                    elif 'pass' in col_lower and 'tds' in col_lower: p_tds = float(row[col])
                    elif 'int' in col_lower: p_ints = float(row[col])
                    elif 'rush' in col_lower and 'yds' in col_lower: r_yds = float(row[col])
                    elif 'rush' in col_lower and 'tds' in col_lower: r_tds = float(row[col])
                    elif 'rec' in col_lower and 'yds' in col_lower: rec_yds = float(row[col])
                    elif 'rec' in col_lower and 'tds' in col_lower: rec_tds = float(row[col])
                    elif 'rec' in col_lower and not 'tgt' in col_lower: rec = float(row[col])
                    elif 'fl' in col_lower: fumbles = float(row[col])

                # Apply FanTeam Math
                fanteam_pts = (
                    (p_yds * 0.04) + (p_tds * 4) + (p_ints * -2) +
                    (r_yds * 0.1) + (r_tds * 6) +
                    (rec * 1) + (rec_yds * 0.1) + (rec_tds * 6) +
                    (fumbles * -2)
                )
                
                all_players.append({
                    'Player': name,
                    'Position': pos.upper(),
                    'Team': team.upper(),
                    'Projected_Points': round(fanteam_pts, 2)
                })
                
        except Exception as e:
            print(f"Failed to scrape {pos.upper()}: {e}")
            
        # Pause for 2 seconds between pages so we don't spam their servers and get banned
        time.sleep(2)

    # 4. Save the new 2026 data over our old baseline file
    final_df = pd.DataFrame(all_players)
    final_df = final_df.sort_values(by='Projected_Points', ascending=False)
    
    output_path = os.path.join("data", "uploads", "baseline_projections.csv")
    final_df.to_csv(output_path, index=False)
    print(f"\nSuccess! 2026 Consensus Projections saved to {output_path}")

if __name__ == "__main__":
    scrape_consensus_projections()