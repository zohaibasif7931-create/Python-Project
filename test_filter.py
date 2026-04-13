import pandas as pd

satisfaction_df = pd.read_csv('satisfaction.csv')
blocked = satisfaction_df[satisfaction_df['stars'] <= -3]

print("=== Blocked entries (stars <= -3) ===")
for idx, row in blocked.iterrows():
    print(f"Model: {row['model']}, Price: {row['price_pta']}, Stars: {row['stars']}")
