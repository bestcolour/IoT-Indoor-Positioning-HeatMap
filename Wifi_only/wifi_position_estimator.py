import os
import sqlite3
import numpy as np
from scipy.optimize import least_squares
from datetime import datetime, timedelta
from wifi_rssi_filter import rssi_to_distance

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

print(f"[INFO] Using database: {DATABASE}")
# AP coordinates
AP_COORDINATES = {
    "RPi_AP_KeeShen": (2.15, 5.84),
    "RPi_AP_Pierre": (0, 5.84),
    "RPi_AP_EnThong": (2.15, 0),
    "RPi_AP_Alicia": (0, 0)
}

def create_position_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_estimated_positions (
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

# Fetch & group RSSI values per device_name using ±2s time window
def fetch_grouped_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT mac, device_name, ap_id, timestamp, filtered_rssi FROM wifi_filtered_rssi ORDER BY timestamp ASC")
    raw_data = cursor.fetchall()
    conn.close()

    grouped = {}
    for mac, device_name, ap_id, ts, rssi in raw_data:
        ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        grouped.setdefault(mac, []).append((ts_dt, device_name, ap_id, rssi))

    windowed_data = {}
    for mac, readings in grouped.items():
        used = set()
        readings.sort(key=lambda x: x[0])  # x[0] is the datetime
        print(f"\n[DEBUG] MAC: {mac} — Total readings: {len(readings)}")
        for entry in readings:
            print(f"  {entry[0]} | AP={entry[2]} | RSSI={entry[3]:.2f}")

        for i, (ts_i, dev_i, ap_i, rssi_i) in enumerate(readings):
            if i in used:
                continue
            window = {ap_i: rssi_i}
            timestamps = [ts_i]
            device_name = dev_i  # Use the first device_name in the group

            for j in range(i + 1, len(readings)):
                ts_j, dev_j, ap_j, rssi_j = readings[j]
                if abs((ts_j - ts_i).total_seconds()) <= 2:
                    window[ap_j] = rssi_j
                    timestamps.append(ts_j)
                    used.add(j)

            if len(window) >= 3:
                mid_ts = min(timestamps) + (max(timestamps) - min(timestamps)) / 2
                ts_str = mid_ts.isoformat()
                if mac not in windowed_data:
                    windowed_data[mac] = {}
                windowed_data[mac][ts_str] = (device_name, window)

    print(f"[DEBUG] Grouped MACs: {len(windowed_data)} with valid trilateration windows")

    return windowed_data  # {mac: {timestamp: (device_name, {ap_id: rssi})}}

# Trilateration (improved + fallback)
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

def weighted_trilateration(ap_positions, distances):
    A, b, weights = [], [], []
    for i in range(1, len(ap_positions)):
        x0, y0 = ap_positions[0]
        xi, yi = ap_positions[i]
        di_sq = distances[i]**2 - distances[0]**2
        A.append([2*(xi - x0), 2*(yi - y0)])
        b.append(di_sq - (xi**2 + yi**2 - x0**2 - y0**2))
        weights.append(1 / (distances[i] + 1e-6))
    try:
        A, b, W = np.array(A), np.array(b), np.diag(weights)
        x = np.linalg.inv(A.T @ W @ A) @ A.T @ W @ b
        return x
    except:
        return None, None

# Position estimation with per-device_name row limiting
def estimate_positions():
    grouped = fetch_grouped_rssi()
    mac_counts = {mac: len(ts_groups) for mac, ts_groups in grouped.items()}
    min_group_count = min(mac_counts.values()) if mac_counts else 0
    print(f"[INFO] Limiting all MAC addresses to {min_group_count} time windows each")

    estimated = {}

    for mac, time_groups in grouped.items():
        limited_time_groups = list(time_groups.items())[:min_group_count]

        for timestamp, (device_name, ap_rssi) in limited_time_groups:
            ap_positions, distances = [], []
            for ap_id, rssi in ap_rssi.items():
                if ap_id in AP_COORDINATES:
                    ap_positions.append(AP_COORDINATES[ap_id])
                    distances.append(rssi_to_distance(rssi))

            if len(ap_positions) == 3:
                result = improved_trilateration(ap_positions, distances)
                if result is None or len(result) != 2:
                    result = weighted_trilateration(ap_positions, distances)

                if result is not None and len(result) == 2:
                    x, y = float(result[0]), float(result[1])
                    estimated[(mac, timestamp)] = (device_name, x, y)
                    print(f"✓ Estimated: MAC={mac}, DEVICE={device_name}, X={x:.2f}, Y={y:.2f}, Time={timestamp}")
                else:
                    print(f"✗ Failed to estimate for MAC={mac} at {timestamp}")

    return estimated  # {(mac, timestamp): (device_name, x, y)}

# Save to DB
def store_positions(positions):
    if not positions:
        print("No new positions to store.")
        return
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for (mac, timestamp), (device_name, x, y) in positions.items():
        cursor.execute("""
            INSERT OR IGNORE INTO wifi_estimated_positions (mac, device_name, x, y, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (mac, device_name, x, y, timestamp))
        print(f"→ Stored: MAC={mac}, DEVICE={device_name}, X={x:.2f}, Y={y:.2f}, Timestamp={timestamp}")
    conn.commit()
    conn.close()
    print(f"{len(positions)} new positions stored.\n")

# Entry point
if __name__ == "__main__":
    create_position_table()
    print("==== Estimating Positions with ±2s Grouping ====")
    try:
        positions = estimate_positions()
        store_positions(positions)
        print("==== Script Completed ====")
    except Exception as e:
        print(f"Error: {e}")
