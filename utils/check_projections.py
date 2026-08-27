import pandas as pd
import os

def check_data():
    file_path = os.path.join("data", "uploads", "baseline_projections.csv")
    
    if not os.path.exists(file_path):
        print("Error: Could not find the CSV.")
        return
        
    df = pd.read_csv(file_path)
    
    print(f"\nTotal Players Projected: {len(df)}")
    
    # Check the top 5 at each position
    positions = ['QB', 'RB', 'WR', 'TE', 'DST']
    
    for pos in positions:
        print(f"\n--- TOP 5 {pos}s ---")
        # Filter by position, take the top 5, and print without the index number
        top_pos = df[df['Position'] == pos].head(5)
        if top_pos.empty:
            print(f"No {pos}s found! (Did you run the DST builder?)")
        else:
            print(top_pos.to_string(index=False))

if __name__ == "__main__":
    check_data()