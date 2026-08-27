import PyPDF2
import pandas as pd
import os
import re

def build_pdf_projections():
    print("Parsing Mike Clay's 2026 Projections PDF...")
    
    # 1. Smarter PDF Locator
    pdf_path = None
    search_folders = ['.', os.path.join('data', 'uploads')]
    
    # Check our search folders for any PDF file
    for folder in search_folders:
        if os.path.exists(folder):
            pdfs_in_folder = [f for f in os.listdir(folder) if f.endswith('.pdf')]
            if pdfs_in_folder:
                pdf_path = os.path.join(folder, pdfs_in_folder[0])
                break
                
    if not pdf_path:
        print("Error: Could not find any .pdf files in your root folder or data/uploads/ folder.")
        print("Please move the Mike Clay PDF into data/uploads/ and run again.")
        return
        
    print(f"Found PDF: {pdf_path}")
    
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        pages = [p.extract_text() for p in reader.pages]

    team_map = {
        'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL', 'Buffalo Bills': 'BUF',
        'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI', 'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE',
        'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
        'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Kansas City Chiefs': 'KC',
        'Los Angeles Chargers': 'LAC', 'Los Angeles Rams': 'LAR', 'Las Vegas Raiders': 'LV', 'Miami Dolphins': 'MIA',
        'Minnesota Vikings': 'MIN', 'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
        'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT', 'Seattle Seahawks': 'SEA',
        'San Francisco 49ers': 'SF', 'Tampa Bay Buccaneers': 'TB', 'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
    }

    qbs, rbs, wrs, tes = [], [], [], []

    print("Extracting Skill Positions...")
    # The Positional Leaderboards are located between pages 35 and 46
    for i in range(34, 46): 
        lines = pages[i].split('\n')
        current_pos = None
        for line in lines:
            # Set the current position based on the table header
            if "Quarterback" in line and "Team" in line: current_pos = 'QB'
            elif "Running Back" in line and "Team" in line: current_pos = 'RB'
            elif "Wide Receiver" in line and "Team" in line: current_pos = 'WR'
            elif "Tight End" in line and "Team" in line: current_pos = 'TE'
            elif current_pos:
                parts = line.split()
                for j, p in enumerate(parts):
                    # We locate the start of the stat columns by finding the first digit
                    if p.isdigit():
                        nums = [x.replace('%', '') for x in parts[j:]]
                        # Verify the rest of the row is pure numbers
                        if all(x.isdigit() for x in nums):
                            name = " ".join(parts[:j-1]).replace("'", "")
                            team = parts[j-1]
                            
                            # Double-check we actually grabbed a valid team code
                            if team.isupper() and len(team) in [2,3]:
                                if current_pos == 'QB' and len(nums) >= 12:
                                    qbs.append({
                                        'Player': name, 'Position': current_pos, 'Team': team,
                                        'Pass_Yds': float(nums[5]), 'Pass_TDs': float(nums[6]), 'INTs': float(nums[7]),
                                        'Rush_Yds': float(nums[10]), 'Rush_TDs': float(nums[11]),
                                        'Rec': 0, 'Rec_Yds': 0, 'Rec_TDs': 0
                                    })
                                elif current_pos != 'QB' and len(nums) >= 10:
                                    player_dict = {
                                        'Player': name, 'Position': current_pos, 'Team': team,
                                        'Pass_Yds': 0, 'Pass_TDs': 0, 'INTs': 0,
                                        'Rush_Yds': float(nums[4]), 'Rush_TDs': float(nums[5]),
                                        'Rec': float(nums[7]), 'Rec_Yds': float(nums[8]), 'Rec_TDs': float(nums[9])
                                    }
                                    if current_pos == 'RB': rbs.append(player_dict)
                                    elif current_pos == 'WR': wrs.append(player_dict)
                                    else: tes.append(player_dict)
                        break

    all_projections = []
    # 2. Apply FanTeam Multipliers
    for p in qbs + rbs + wrs + tes:
        ft_pts = (p['Pass_Yds'] * 0.04) + (p['Pass_TDs'] * 4) + (p['INTs'] * -2) + (p['Rush_Yds'] * 0.1) + (p['Rush_TDs'] * 6) + (p['Rec'] * 1) + (p['Rec_Yds'] * 0.1) + (p['Rec_TDs'] * 6)
        p['Projected_Points'] = round(ft_pts, 2)
        all_projections.append(p)

    print("Extracting Defenses (DST)...")
    # 3. Pull Team Defense Totals (Pages 2-33)
    for i in range(1, 33):
        text = pages[i]
        
        current_team_code = 'UNK'
        team_header = [l for l in text.split('\n') if 'Projections' in l and '2026' in l]
        if team_header:
            header_str = team_header[0]
            for team_full, code in team_map.items():
                if team_full in header_str:
                    current_team_code = code
                    break
                    
        sacks = 0.0
        ints = 0.0
        pa = 0.0
        
        # Scrape Defensive Totals line (e.g. Total 11772 1031 36.0 12.4)
        m_def = re.search(r"Total\s+(11\d{3})\s+(\d{3,4})\s+([\d\.]+)\s+([\d\.]+)", text)
        if m_def:
            sacks = float(m_def.group(3))
            ints = float(m_def.group(4))
        
        # Scrape Schedule Points Allowed (e.g. Total 305 465 21%)
        m_sch = re.search(r"Total\s+(\d{3,4})\s+(\d{3,4})\s+\d+%", text)
        if m_sch:
            pa = float(m_sch.group(2))
            
        if pa > 0:
            pa_per_game = pa / 17.0
            
            def calc_bracket(pts):
                if pts < 1: return 10
                elif pts <= 6: return 7
                elif pts <= 13: return 4
                elif pts <= 20: return 1
                elif pts <= 27: return 0
                elif pts <= 34: return -1
                else: return -4
            
            total_bracket_pts = calc_bracket(pa_per_game) * 17
            dst_pts = (sacks * 1) + (ints * 2) + total_bracket_pts
            
            all_projections.append({
                'Player': f"{current_team_code} DST",
                'Position': 'DST',
                'Team': current_team_code,
                'Projected_Points': round(dst_pts, 2)
            })

    # 4. Final Format and Export
    final_df = pd.DataFrame(all_projections)
    final_df = final_df[['Player', 'Position', 'Team', 'Projected_Points']]
    final_df = final_df.sort_values(by='Projected_Points', ascending=False)
    
    # Overwrite the old baseline file so the Optimizer finds it immediately
    output_path = os.path.join("data", "uploads", "baseline_projections.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    
    print(f"Success! Generated 2026 projections for {len(final_df)} players/DSTs.")
    print(f"Saved directly to {output_path}")

if __name__ == "__main__":
    build_pdf_projections()