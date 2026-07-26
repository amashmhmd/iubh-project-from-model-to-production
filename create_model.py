"""
create_model.py
----------------
Trains a simple anomaly-detection model and saves it to a file, so it can later
be loaded by the Flask API (Section 2) - exactly the pattern from the reference video.

Model = a scikit-learn Pipeline with two steps:
  1. StandardScaler  -> puts temperature/humidity/sound on a comparable scale
  2. IsolationForest -> the actual anomaly detector

Bundling both into ONE pipeline means we pickle a single object, and the API can
just call .predict() / .score_samples() without re-doing any preprocessing.
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

FEATURES = ["temperature", "humidity", "sound"]

# 1) Load the data we generated.
data = pd.read_csv("sensor_data.csv")
X = data[FEATURES]                 # the model only sees the 3 sensor readings
y_true = data["is_anomaly"]        # ground truth, used ONLY for evaluation below

# 2) Build and train the model.
#    contamination = the share of points we expect to be anomalies (~2%).
#    IsolationForest is unsupervised: notice we call fit(X) WITHOUT the labels y.
model = Pipeline([
    ("scaler", StandardScaler()),
    ("detector", IsolationForest(
        n_estimators=100,
        contamination=0.02,
        random_state=42,
    )),
])
model.fit(X)

# 3) Check basic statistical measures (required by the task).
#    IsolationForest.predict() returns  1 = normal, -1 = anomaly.
#    We convert that to 1 = anomaly to compare against our ground-truth labels.
raw_pred = model.predict(X)
y_pred = np.where(raw_pred == -1, 1, 0)

print("Confusion matrix (rows = actual, cols = predicted):")
print(confusion_matrix(y_true, y_pred))
print("\nClassification report:")
print(classification_report(y_true, y_pred, target_names=["normal", "anomaly"]))

# score_samples: higher = more normal. We negate it so higher = more anomalous,
# which is the intuitive "anomaly score" we will return from the API.
scores = -model.score_samples(X)
print(f"Anomaly score range: min={scores.min():.3f}, max={scores.max():.3f}, "
      f"mean={scores.mean():.3f}")

# 4) Save the trained pipeline to a file (this is our 'model1.pickle' equivalent).
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("\nSaved trained model to model.pkl")
