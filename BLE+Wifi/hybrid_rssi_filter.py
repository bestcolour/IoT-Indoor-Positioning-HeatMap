import os
import sqlite3
import numpy as np
from collections import defaultdict
from datetime import datetime

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

# Kalman Filter class
class KalmanFilter:
    def __init__(self, process_variance=1e-3, measurement_variance=2.0):
        self.x = -70
        self.P = 1.0
        self.Q = process_variance
        self.R = measurement_variance

    def update(self, measurement):
        self.P += self.Q
        K = self.P / (self.P + self.R)
        self.x += K * (measurement - self.x)
        self.P *= (1 - K)
        return self.x

# Global Kalman filter store
kalman_filters = {}

def get_kalman_filter(device_name, ap_id):
    key = (device_name, ap_id)
    if key not in kalman_filters:
        kalman_filters[key] = KalmanFilter()
    return kalman_filters[key]

def normalize_device_name(name):
    name = name.strip()
    if "MSStick" in name:
        name = name.replace("MSStick", "M5Stick")
    if "_BLE_" in name:
        base_name = name.split("_BLE_")[-1]
        if "SeeShen" in base_name:
            base_name = "KeeShen"
        return f"M5_{base_name}"
    if "CPlus-" in name:
        return f"M5_{name.split('CPlus-')[-1]}"
    return name

def normalize_ap_id(ap_id):
    ap_id = ap_id.strip().lower()
    mapping = {
        "xypi": "RPi_AP_XY",
        "aliciapi": "RPi_AP_Alicia",
        "enthong": "RPi_AP_EnThong",
        "pierre": "RPi_AP_Pierre",
        "rpi_hybrid_pierre": "RPi_AP_Pierre",
        "rpi_hybrid_alicia": "RPi_AP_Alicia",
        "rpi_hybrid_xinyi": "RPi_AP_XY",
        "rpi_hybrid_enthong": "RPi_AP_EnThong"
    }
    return mapping.get(ap_id, ap_id)

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hybrid_filtered_rssi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            ap_id TEXT,
            device_name TEXT,
            filtered_rssi REAL,
            latency REAL,
            UNIQUE(timestamp, ap_id, device_name)
        )
    """)
    conn.commit()
    conn.close()

def fetch_raw_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(""" 
        SELECT timestamp, ap_id, mac, device_name, rssi, latency, 'BLE' AS signal_type FROM ble_rssi 
        UNION ALL 
        SELECT timestamp, ap_id, mac, device_name, rssi, latency, 'WiFi' AS signal_type FROM wifi_rssi 
        ORDER BY timestamp ASC
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def merge_and_filter_rssi():
    create_tables()
    raw_data = fetch_raw_rssi()

    grouped = defaultdict(list)
    for timestamp, ap_id, _, device_name, rssi, latency, signal_type in raw_data:
        ap_id = normalize_ap_id(ap_id)
        device_name = normalize_device_name(device_name)
        ts_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        grouped[(device_name, ap_id)].append((ts_dt, rssi, latency, signal_type))

    filtered_entries = []

    for (device_name, ap_id), readings in grouped.items():
        ble = [(ts, rssi, lat) for ts, rssi, lat, t in readings if t == 'BLE']
        wifi = [(ts, rssi, lat) for ts, rssi, lat, t in readings if t == 'WiFi']

        all_timestamps = sorted(set([ts for ts, _, _ in ble] + [ts for ts, _, _ in wifi]))

        for ts in all_timestamps:
            nearby_ble = [(rssi, lat) for ts_ble, rssi, lat in ble if abs((ts_ble - ts).total_seconds()) <= 2]
            nearby_wifi = [(rssi, lat) for ts_wifi, rssi, lat in wifi if abs((ts_wifi - ts).total_seconds()) <= 2]

            if nearby_ble and nearby_wifi:
                avg_ble = np.mean([r for r, _ in nearby_ble])
                avg_wifi = np.mean([r for r, _ in nearby_wifi])
                avg_ble_lat = np.mean([lat for _, lat in nearby_ble])
                avg_wifi_lat = np.mean([lat for _, lat in nearby_wifi])
                fused_latency = (avg_ble_lat + avg_wifi_lat) / 2

                ble_kf = get_kalman_filter(device_name, ap_id + "_BLE")
                wifi_kf = get_kalman_filter(device_name, ap_id + "_WiFi")

                filtered_ble = ble_kf.update(avg_ble)
                filtered_wifi = wifi_kf.update(avg_wifi)

                fused_rssi = (filtered_ble + filtered_wifi) / 2

                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                filtered_entries.append((ts_str, ap_id, device_name, fused_rssi, fused_latency))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO hybrid_filtered_rssi
        (timestamp, ap_id, device_name, filtered_rssi, latency)
        VALUES (?, ?, ?, ?, ?)
    """, filtered_entries)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    merge_and_filter_rssi()
