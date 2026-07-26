"""
stream_simulator.py
--------------------
Simulates the continuous data stream from the factory sensors (task step 2,
option 1: "run an application on your local machine which produces a continuous
stream of simulated sensor data").

Every ~1 second it:
  1. generates one new sensor reading (mostly normal, occasionally a fault),
  2. POSTs it to the running Flask API,
  3. reads back the anomaly score,
  4. prints it and raises an ALERT if the item is flagged.

Start app.py FIRST (in another terminal), then run:  python stream_simulator.py
Stop it any time with Ctrl+C.
"""

import time
import random
import requests

API_URL = "http://127.0.0.1:5000/predict"

# How often a generated reading is deliberately a fault (10% here, for a lively demo).
ANOMALY_PROBABILITY = 0.10


def generate_reading():
    """Produce one sensor reading. Most are normal; some are clear faults."""
    if random.random() < ANOMALY_PROBABILITY:
        # An anomalous item: at least one reading is far from normal.
        return {
            "temperature": round(random.gauss(85, 6), 2),
            "humidity":    round(random.gauss(70, 8), 2),
            "sound":       round(random.gauss(92, 7), 2),
        }
    # A normal item.
    return {
        "temperature": round(random.gauss(65, 4), 2),
        "humidity":    round(random.gauss(45, 6), 2),
        "sound":       round(random.gauss(70, 5), 2),
    }


def run_stream():
    print("Streaming sensor data to the API. Press Ctrl+C to stop.\n")
    item_id = 0
    while True:
        item_id += 1
        reading = generate_reading()

        try:
            response = requests.post(API_URL, json=reading, timeout=5)
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"  [!] Could not reach the API: {e}. Is app.py running?")
            time.sleep(2)
            continue

        score = result["anomaly_score"]
        flag = result["is_anomaly"]
        status = " <-- ALERT: anomaly detected!" if flag else ""
        print(f"item {item_id:>4} | T={reading['temperature']:>5} "
              f"H={reading['humidity']:>5} S={reading['sound']:>5} "
              f"| score={score:.3f}{status}")

        time.sleep(1)  # one reading per second


if __name__ == "__main__":
    try:
        run_stream()
    except KeyboardInterrupt:
        print("\nStream stopped.")
