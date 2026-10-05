"""
generate_data.py
-----------------
The dataset is created to imitate factory sensor readings for each produced item. 
It includes measurements for **temperature, humidity, and sound volume**, 
representing the operating conditions of the factory machines.

The task allows the use of fictional sample data, so the data is created for this purpose. 
Most of the items have **normal sensor readings**, while a small number are intentionally generated as 
**anomalies** with unusual values. 
For example, some items may have a very high temperature, which could represent an overheating machine, 
while others may have an unusually high sound volume, indicating that a machine is operating abnormally.

An **`is_anomaly`** column is also included as the ground truth. 
This column shows whether each item was intentionally created as normal or anomalous. 
The model does **not use this column during training**, since the task is based on unsupervised anomaly detection. 
It is only used later to check how well the model detects the anomalies that were added to the dataset.

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
