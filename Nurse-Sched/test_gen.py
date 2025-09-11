import pandas as pd
import numpy as np

# Example nurse names
nurses = [
    "Alice", "Bob", "Charlie", "Diana", "Eve",
    "Frank", "Grace", "Hank", "Ivy", "Jack",
    "Karen", "Leo", "Mia", "Nina", "Oscar",
    "Paul", "Quinn", "Rachel", "Steve", "Tina",
    "Nicole", "Xavier", "Renee", "Sarah", "Yahaira"
]

num_days = 30
days = [f"Day{d+1}" for d in range(num_days)]

# Random preferences: 1 = prefers, 0 = off
prefs = pd.DataFrame(index=nurses, columns=days)

for n in nurses:
    # Each nurse prefers roughly half the days
    prefs.loc[n] = np.random.choice([0, 1], size=num_days, p=[0.5, 0.5])

# Save to CSV
prefs.to_csv("sample_preferences_named.csv")
print("Sample CSV generated: sample_preferences_named.csv")
