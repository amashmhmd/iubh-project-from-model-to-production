"""
generate_data.py
-----------------
Creates a sample dataset that imitates the factory sensors described in the task:
temperature, humidity and sound volume measured for each produced item.

We invent the data ourselves (the task explicitly allows "fictional sample data").
Most items are NORMAL. A small fraction are ANOMALIES with shifted readings,
e.g. an overheating or unusually loud machine.

We also save a column 'is_anomaly' as GROUND TRUTH. The model itself will NOT use
this column (anomaly detection is unsupervised) - we only keep it so that later we
can check whether the model actually catches the anomalies we planted.
"""

import numpy as np
import pandas as pd

# A fixed seed makes the data reproducible: you get the same numbers every run.
rng = np.random.default_rng(seed=42)

N_NORMAL = 2000      # number of normal items
N_ANOMALY = 40       # number of faulty items (~2% -> realistic for a factory)

# --- Normal items: readings cluster around typical operating values ---
normal = pd.DataFrame({
    "temperature": rng.normal(loc=65, scale=4, size=N_NORMAL),   # degrees Celsius
    "humidity":    rng.normal(loc=45, scale=6, size=N_NORMAL),   # percent
    "sound":       rng.normal(loc=70, scale=5, size=N_NORMAL),   # decibels
    "is_anomaly":  0,
})

# --- Anomalous items: at least one reading is clearly off ---
anomaly = pd.DataFrame({
    "temperature": rng.normal(loc=85, scale=6, size=N_ANOMALY),  # machine overheating
    "humidity":    rng.normal(loc=70, scale=8, size=N_ANOMALY),  # damp / leak
    "sound":       rng.normal(loc=92, scale=7, size=N_ANOMALY),  # grinding / loud fault
    "is_anomaly":  1,
})

# Combine and shuffle so the anomalies are spread throughout the file.
data = pd.concat([normal, anomaly], ignore_index=True)
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

# Round to look like real sensor output.
for col in ["temperature", "humidity", "sound"]:
    data[col] = data[col].round(2)

data.to_csv("sensor_data.csv", index=False)

print(f"Saved sensor_data.csv with {len(data)} rows "
      f"({data['is_anomaly'].sum()} anomalies, "
      f"{100 * data['is_anomaly'].mean():.1f}% of the data).")
print(data.head())
