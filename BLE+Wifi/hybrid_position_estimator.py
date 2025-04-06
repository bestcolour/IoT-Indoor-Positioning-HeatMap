import os
import sqlite3
import numpy as np
from datetime import datetime
from scipy.optimize import least_squares

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

AP_COORDINATES = {
    "RPi_AP_XY": (4.96, 0),
    "RPi_AP_Pierre": (4.96, 8.06),
    "RPi_AP_EnThong": (0, 8.06),
    "RPi_AP_Alicia": (0, 0),
}

# Fixed RSSI-to-distance parameters (as requested)
A = -55.525   # Reference RSSI at 1m
n = 0.735     # Path-loss exponent

def rssi_to_distance(rssi):
    """Convert RSSI to distance using fixed parameters A and n."""
    return 10 ** ((A - rssi) / (10 * n))

def robust_trilateration(ap_positions, distances):
    """Weighted nonlinear least-squares trilateration."""
    points = np.array(ap_positions)
    dists = np.array(distances)
    weights = 1.0 / (dists + 0.1)  # Closer APs have higher weight

    def cost_fn(point):
        return weights * (np.linalg.norm(points - point, axis=1) - dists)

    try:
        bounds = ([0, 0], [4.96, 8.06]) 
        result = least_squares(
            cost_fn,
            x0=np.median(points, axis=0),
            bounds=bounds,
            loss='soft_l1',
            max_nfev=200
        )
        return result.x if result.success else None
    except Exception as e:
        print(f"Trilateration failed: {e}")
        return None

def fetch_grouped_rssi(device_name, time_window=2):
    """Fetch RSSI readings for a device, grouped by timestamp windows."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, ap_id, filtered_rssi 
        FROM hybrid_filtered_rssi
        WHERE device_name = ?
        ORDER BY timestamp ASC
    """, (device_name,))
    raw_data = cursor.fetchall()
    conn.close()

    grouped = []
    for ts, ap_id, rssi in raw_data:
        ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        grouped.append((ts_dt, ap_id, rssi))
    
    # Group readings within ±time_window seconds
    windowed = []
    i = 0
    while i < len(grouped):
        ts_i, ap_i, rssi_i = grouped[i]
        window = {ap_i: rssi_i}
        timestamps = [ts_i]
        j = i + 1
        while j < len(grouped):
            ts_j, ap_j, rssi_j = grouped[j]
            if abs((ts_j - ts_i).total_seconds()) <= time_window:
                window[ap_j] = rssi_j
                timestamps.append(ts_j)
                j += 1
            else:
                break
        if len(window) >= 3:  # Require ≥3 APs for trilateration
            mid_ts = min(timestamps) + (max(timestamps) - min(timestamps)) / 2
            windowed.append((mid_ts, window))
        i = j
    return windowed

def estimate_positions():
    """Main function to estimate and store positions."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT device_name, ap_id, timestamp, filtered_rssi 
        FROM hybrid_filtered_rssi 
        LIMIT 10
    """)
    print("Sample RSSI data:")
    for row in cursor.fetchall():
        print(row)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hybrid_estimated_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            x REAL,
            y REAL,
            timestamp DATETIME,
            method TEXT,
            UNIQUE(device_name, timestamp)
        )
    """)
    
    # Get all devices with Kalman-filtered RSSI
    cursor.execute("SELECT DISTINCT device_name FROM hybrid_filtered_rssi")
    devices = [row[0] for row in cursor.fetchall()]

    for device in devices:
        rssi_groups = fetch_grouped_rssi(device)

        for ts, ap_rssi in rssi_groups:
            ap_positions, distances = [], []
            for ap_id, rssi in ap_rssi.items():
                if ap_id in AP_COORDINATES:
                    ap_positions.append(AP_COORDINATES[ap_id])
                    distances.append(rssi_to_distance(rssi))

            if len(ap_positions) >= 3:
                position = robust_trilateration(ap_positions, distances)
                if position is not None:
                    x, y = position[0], position[1]  # Direct trilateration result
                    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT OR IGNORE INTO hybrid_estimated_positions
                        (device_name, x, y, timestamp, method)
                        VALUES (?, ?, ?, ?, ?)
                    """, (device, x, y, ts_str, "trilateration"))
                    print(f"{device} @ {ts_str} → X={x:.2f}, Y={y:.2f}")

    conn.commit()
    conn.close()
    print("✅ Position estimation completed.")

if __name__ == "__main__":
    estimate_positions()