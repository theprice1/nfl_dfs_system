import pandas as pd
import pulp
import os

def run_season_optimizer():
    file_path = os.path.join("data", "outputs", "master_player_list.csv")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("Error: Could not find master_player_list.csv. Run data_handler.py first.")
        return

    print("Initializing PuLP Engine with 140M Budget...")
    prob = pulp.LpProblem("FanTeam_Season_Long", pulp.LpMaximize)
    
    # 1. Variables
    player_vars = {}
    for i, row in df.iterrows():
        player_vars[i] = pulp.LpVariable(f"player_{i}", cat="Binary")
        
    # 2. Objective Function
    prob += pulp.lpSum([df.loc[i, 'Projected_Points'] * player_vars[i] for i in df.index])
    
    # 3. Base Positional Constraints
    prob += pulp.lpSum([player_vars[i] for i in df.index]) == 9
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'QB']) == 1
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'DST']) == 1
    
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'RB']) >= 2
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'RB']) <= 3
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'WR']) >= 3
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'WR']) <= 4
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'TE']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Position'] == 'TE']) <= 2
    
    # 4. NEW: Budget Constraint (Max 140M)
    prob += pulp.lpSum([df.loc[i, 'Price'] * player_vars[i] for i in df.index]) <= 140.0
    
    # 5. NEW: Max 3 players from the same team
    teams = df['Team'].unique()
    for team in teams:
        prob += pulp.lpSum([player_vars[i] for i in df.index if df.loc[i, 'Team'] == team]) <= 3

    print("Calculating optimal Week 1 lineup...")
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    # 6. Format Output
    if pulp.LpStatus[prob.status] == 'Optimal':
        print("\n--- OPTIMAL SEASON-LONG LINEUP (140M BUDGET) ---")
        total_points = 0
        total_salary = 0
        
        lineup = []
        for i in df.index:
            if player_vars[i].varValue == 1:
                lineup.append({
                    'Pos': df.loc[i, 'Position'],
                    'Player': df.loc[i, 'Player'],
                    'Team': df.loc[i, 'Team'],
                    'Price': df.loc[i, 'Price'],
                    'Pts': df.loc[i, 'Projected_Points']
                })
        
        sort_order = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4, 'DST': 5}
        lineup = sorted(lineup, key=lambda x: sort_order[x['Pos']])
        
        for p in lineup:
            print(f"{p['Pos']:<3} | {p['Player']:<22} ({p['Team']:<3}) | ${p['Price']:>4}M | {p['Pts']:>6} pts")
            total_points += p['Pts']
            total_salary += p['Price']
            
        print(f"-------------------------------------------------------")
        print(f"REMAINING BUDGET: ${140.0 - total_salary:.1f}M")
        print(f"TOTAL PROJECTED POINTS: {total_points:.2f}\n")
    else:
        print("Could not find an optimal solution. Check constraints.")

if __name__ == "__main__":
    run_season_optimizer()