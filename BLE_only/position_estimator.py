import os
import sqlite3
import numpy as np
from scipy.optimize import least_squares
from datetime import datetime
from collections import defaultdict
from rssi_filter import rssi_to_distance

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

# AP coordinates
AP_COORDINATES = {
    "xypi": (4.96, 0),
    "pierre": (4.96, 8.06),
    "enthong": (0, 8.06),
    "aliciapi": (0, 0)
}

# Create estimated_positions table with device_name
def create_position_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estimated_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            device_name TEXT,
            x REAL,
            y REAL,
            timestamp DATETIME,
            UNIQUE(mac, timestamp)
        )
    """)
    conn.commit()
    conn.close()

# Group RSSI readings by MAC within ±2s window
def fetch_grouped_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mac, device_name, ap_id, timestamp, filtered_rssi
        FROM filtered_rssi
        ORDER BY timestamp ASC
    """)
    raw_data = cursor.fetchall()
    conn.close()

    grouped = defaultdict(list)
    for mac, device_name, ap_id, ts, rssi in raw_data:
        ts_dt = datetime.fromisoformat(ts)
        grouped[mac].append((ts_dt, ap_id, rssi, device_name))

    windowed_data = {}
    mac_device_name = {}

    for mac, readings in grouped.items():
        readings.sort()
        i = 0
        while i < len(readings):
            ts_i, ap_i, rssi_i, dev_name = readings[i]
            window = {ap_i: rssi_i}
            timestamps = [ts_i]
            j = i + 1

            while j < len(readings):
                ts_j, ap_j, rssi_j, _ = readings[j]
                if (ts_j - ts_i).total_seconds() <= 3:
                    window[ap_j] = rssi_j
                    timestamps.append(ts_j)
                    j += 1
                else:
                    break

            if len(window) == 3:
                mid_ts = min(timestamps) + (max(timestamps) - min(timestamps)) / 2
                ts_str = mid_ts.isoformat()

                if mac not in windowed_data:
                    windowed_data[mac] = {}
                    mac_device_name[mac] = dev_name

                windowed_data[mac][ts_str] = window
                i = j  # Skip overlapping
            else:
                i += 1

    return windowed_data, mac_device_name

# Nonlinear least squares trilateration
def improved_trilateration(ap_positions, distances):
    points = np.array(ap_positions)
    dists = np.array(distances)
    weights = 1.0 / (dists + 0.1)

    def residuals(point):
        return weights * (np.linalg.norm(points - point, axis=1) - dists)

    try:
        initial = np.mean(points, axis=0)
        result = least_squares(residuals, initial, method='lm')
        return result.x if result.success else (None, None)
    except:
        return None, None

# Linear fallback trilateration
def weighted_trilateration(ap_positions, distances):
    A, b, weights = [], [], []
    for i in range(1, len(ap_positions)):
        x0, y0 = ap_positions[0]
        xi, yi = ap_positions[i]
        di_sq = distances[i]**2 - distances[0]**2
        A.append([2 * (xi - x0), 2 * (yi - y0)])
        b.append(di_sq - (xi**2 + yi**2 - x0**2 - y0**2))
        weights.append(1 / (distances[i] + 1e-6))
    try:
        A, b, W = np.array(A), np.array(b), np.diag(weights)
        x = np.linalg.inv(A.T @ W @ A) @ A.T @ W @ b
        return x
    except:
        return None, None

# Estimate positions from grouped RSSI data
def estimate_positions():
    grouped, mac_device_name = fetch_grouped_rssi()
    estimated = {}

    for mac, time_groups in grouped.items():
        device_name = mac_device_name.get(mac, "Unknown")
        for timestamp, ap_rssi in time_groups.items():
            ap_positions, distances = [], []
            for ap_id, rssi in ap_rssi.items():
                if ap_id in AP_COORDINATES:
                    ap_positions.append(AP_COORDINATES[ap_id])
                    distances.append(rssi_to_distance(rssi))

            if len(ap_positions) >= 3:
                result = improved_trilateration(ap_positions, distances)
                if result is None or len(result) != 2:
                    result = weighted_trilateration(ap_positions, distances)

                if result is not None and len(result) == 2:
                    x, y = float(result[0]), float(result[1])
                    estimated[(mac, timestamp)] = (x, y, device_name)
                    print(f"✓ Estimated: MAC={mac}, Name={device_name}, X={x:.2f}, Y={y:.2f}, Time={timestamp}")
                else:
                    print(f"✗ Failed to estimate for MAC={mac} at {timestamp}")

    return estimated

# Store estimated positions to DB
def store_positions(positions):
    if not positions:
        print("No new positions to store.")
        return
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for (mac, timestamp), (x, y, device_name) in positions.items():
        cursor.execute("""
            INSERT OR IGNORE INTO estimated_positions (mac, device_name, x, y, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (mac, device_name, x, y, timestamp))
        print(f"→ Stored: MAC={mac}, Name={device_name}, X={x:.2f}, Y={y:.2f}, Timestamp={timestamp}")
    conn.commit()
    conn.close()
    print(f"{len(positions)} new positions stored.\n")

# Entry point
if __name__ == "__main__":
    create_position_table()
    print("==== Estimating Positions (±2s Window, ≥3 APs) ====")
    try:
        results = estimate_positions()
        store_positions(results)
        print("==== Done ====")
    except Exception as ex:
        print("Error:", ex)
