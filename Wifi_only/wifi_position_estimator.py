import os
import sqlite3
import numpy as np
from scipy.optimize import least_squares
from datetime import datetime
from wifi_rssi_filter import rssi_to_distance

# 1) Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

# 2) AP coordinates for each ap_id in your DB.
#    Make sure these keys match what's actually in your "ap_id" column.
AP_COORDINATES = {
    "RPi_AP_XY": (4.96, 0),
    "RPi_AP_Pierre": (4.96, 8.06),
    "RPi_AP_EnThong": (0, 8.06),
    "RPi_AP_Alicia": (0, 0)
}

def create_position_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_estimated_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            x REAL,
            y REAL,
            timestamp DATETIME,
            device_name TEXT,
            UNIQUE(mac, timestamp)
        )
    """)
    conn.commit()
    conn.close()


# 3) Fetch & group RSSI values per device_name using ±2s window
def fetch_grouped_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Pull data from your wifi_filtered_rssi table:
    cursor.execute("""
        SELECT device_name, mac, ap_id, timestamp, filtered_rssi
        FROM wifi_filtered_rssi
        ORDER BY timestamp ASC
    """)
    raw_data = cursor.fetchall()
    conn.close()

    # Group by device_name => { "M5StickCPlus-KeeShen": [(datetime, ap_id, rssi), ...], ... }
    grouped = {}
    for device_name, mac, ap_id, ts, rssi in raw_data:
        # If timestamps are "YYYY-MM-DD HH:MM:SS":
        ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        grouped.setdefault(device_name, []).append((ts_dt, ap_id, rssi))

    # Bucket into ±2s windows => {device_name: {timestamp: {ap_id: rssi, ...}}, ...}
    windowed_data = {}
    for device_name, readings in grouped.items():
        used = set()
        # Sort by datetime
        readings.sort(key=lambda x: x[0])

        for i, (ts_i, ap_i, rssi_i) in enumerate(readings):
            if i in used:
                continue

            # Start a window from this reading
            window = {ap_i: rssi_i}
            timestamps = [ts_i]

            # Collect subsequent readings if within 2s
            for j in range(i + 1, len(readings)):
                ts_j, ap_j, rssi_j = readings[j]
                if abs((ts_j - ts_i).total_seconds()) <= 2:
                    window[ap_j] = rssi_j
                    timestamps.append(ts_j)
                    used.add(j)

            # Keep only if == 3 APs in this time window
            if len(window) == 3:
                # Calculate a "midpoint" timestamp
                min_t, max_t = min(timestamps), max(timestamps)
                mid_ts = min_t + (max_t - min_t) / 2
                ts_str = mid_ts.strftime("%Y-%m-%d %H:%M:%S")

                if device_name not in windowed_data:
                    windowed_data[device_name] = {}
                windowed_data[device_name][ts_str] = window

    return windowed_data


# 4) Trilateration methods
def improved_trilateration(ap_positions, distances):
    """Nonlinear least-squares solution."""
    points = np.array(ap_positions)
    dists = np.array(distances)
    # Weight shorter distances more heavily
    weights = 1.0 / (dists + 0.1)

    def residuals(point):
        return weights * (np.linalg.norm(points - point, axis=1) - dists)

    try:
        initial = np.mean(points, axis=0)
        result = least_squares(residuals, initial, method='lm')
        return result.x if result.success else (None, None)
    except:
        return (None, None)


def weighted_trilateration(ap_positions, distances):
    """Linear, weighted approach."""
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
        return (None, None)


# 5) Estimating positions
def estimate_positions():
    windowed = fetch_grouped_rssi()
    estimated = {}

    for device_name, time_groups in windowed.items():
        for ts_str, ap_rssi_dict in time_groups.items():
            ap_positions, distances = [], []
            for ap_id, rssi in ap_rssi_dict.items():
                if ap_id in AP_COORDINATES:
                    ap_positions.append(AP_COORDINATES[ap_id])
                    dist = rssi_to_distance(rssi)
                    distances.append(dist)

            if len(ap_positions) >= 3:
                result = improved_trilateration(ap_positions, distances)
                if result is None or len(result) != 2:
                    result = weighted_trilateration(ap_positions, distances)

                if result is not None and len(result) == 2:
                    x, y = float(result[0]), float(result[1])
                    mac = find_mac_for_device_at_time(device_name, ts_str)
                    if mac:
                        estimated[(device_name, mac, ts_str)] = (x, y)
                        print(f"{device_name} ({mac}) @ {ts_str}: X={x:.2f}, Y={y:.2f}")
                    else:
                        print(f"No MAC found for {device_name} @ {ts_str}")
                else:
                    print(f"Trilateration failed for {device_name} @ {ts_str}")

    return estimated


# 6) Store results
def store_positions(positions):
    if not positions:
        print("No new positions to store.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for (device_name, mac, ts_str), (x, y) in positions.items():
        cursor.execute("""
            INSERT OR IGNORE INTO wifi_estimated_positions (mac, x, y, timestamp, device_name)
            VALUES (?, ?, ?, ?, ?)
        """, (mac, x, y, ts_str, device_name))
        print(f"→ Stored: {device_name} ({mac}) @ {ts_str} => X={x:.2f}, Y={y:.2f}")

    conn.commit()
    conn.close()
    print(f"{len(positions)} new positions stored.")

def find_mac_for_device_at_time(device_name, timestamp_str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mac FROM wifi_filtered_rssi
        WHERE device_name = ?
        AND ABS(strftime('%s', timestamp) - strftime('%s', ?)) <= 2
        ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?)) ASC
        LIMIT 1
    """, (device_name, timestamp_str, timestamp_str))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# 7) Main
if __name__ == "__main__":
    create_position_table()
    print("==== Estimating Positions (±2s Window, ≥3 APs) ====")
    try:
        results = estimate_positions()
        store_positions(results)
        print("==== Done ====")
    except Exception as ex:
        print("Error:", ex)
