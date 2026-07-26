"""
app.py
-------
Wraps the trained anomaly-detection model in a RESTful API using Flask.
This is the direct equivalent of the app.py shown in the reference video, adapted
for sensor data and extended with a health check and request logging.

Routes:
  GET  /health   -> simple status check (used for monitoring / uptime checks)
  POST /predict  -> send sensor readings as JSON, get an anomaly score back

Run with:   python app.py
The API then listens on http://127.0.0.1:5000
"""

import pickle
import logging
import datetime
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

FEATURES = ["temperature", "humidity", "sound"]

# --- Load the model once, at start-up (not on every request -> faster) ---
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# --- Set up logging so every prediction is recorded (monitorability) ---
logging.basicConfig(
    filename="predictions.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

app = Flask(__name__)


class BadRequest(Exception):
    """Raised when the incoming JSON does not match the expected contract."""


def validate(rows):
    """Check the request body against the API contract before it reaches the model.

    Without this, a missing or non-numeric field raises deep inside pandas and
    Flask returns a bare 500 with a stack trace - unhelpful to the caller and a
    poor contract for a service other systems depend on. We fail fast instead,
    with a 400 that names exactly what was wrong.
    """
    if not rows:
        raise BadRequest("Request body is empty; expected a reading or a list of readings.")

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise BadRequest(f"Reading {i} is not a JSON object.")

        missing = [f for f in FEATURES if f not in row]
        if missing:
            raise BadRequest(f"Reading {i} is missing required field(s): {', '.join(missing)}.")

        for f in FEATURES:
            try:
                float(row[f])
            except (TypeError, ValueError):
                raise BadRequest(f"Reading {i}: field '{f}' must be numeric, got {row[f]!r}.")


def score_readings(rows):
    """Take a list of reading-dicts, return anomaly scores and flags.

    rows = [{"temperature": 65, "humidity": 45, "sound": 70}, ...]
    """
    X = pd.DataFrame(rows)[FEATURES]

    # predict(): 1 = normal, -1 = anomaly  -> we turn it into a boolean flag.
    is_anomaly = (model.predict(X) == -1)

    # score_samples(): higher = more normal. We negate it so that a HIGHER
    # number means MORE anomalous, which is the intuitive 'anomaly score'.
    scores = -model.score_samples(X)

    return is_anomaly, scores


@app.route("/health", methods=["GET"])
def health():
    """Lets a monitoring tool confirm the service is alive."""
    return jsonify({"status": "ok", "time": datetime.datetime.now().isoformat()})


@app.route("/predict", methods=["POST"])
def predict():
    """Receive sensor readings as JSON and return anomaly predictions.

    Accepts either a single reading:
        {"temperature": 86.1, "humidity": 72.0, "sound": 95.3}
    or a list of readings (a batch):
        [{"temperature": ...}, {"temperature": ...}]
    """
    data = request.get_json(force=True)

    # Normalise input to a list so we can handle single readings and batches alike.
    rows = data if isinstance(data, list) else [data]

    is_anomaly, scores = score_readings(rows)

    results = []
    for row, flag, score in zip(rows, is_anomaly, scores):
        results.append({
            "input": row,
            "anomaly_score": round(float(score), 4),
            "is_anomaly": bool(flag),
        })
        logging.info(f"input={row} score={float(score):.4f} anomaly={bool(flag)}")

    # Return a single object for a single reading, a list for a batch.
    payload = results[0] if not isinstance(data, list) else results
    return jsonify(payload)


if __name__ == "__main__":
    # host=0.0.0.0 would expose it on the network; 127.0.0.1 keeps it local for testing.
    app.run(host="127.0.0.1", port=5000, debug=False)
