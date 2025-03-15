import sqlite3
import numpy as np
import time

DATABASE = "BLE_only/positioning.db"  # Ensure correct path

# Kalman Filter for RSSI Smoothing
class KalmanFilter:
    def __init__(self, process_variance=1e-3, measurement_variance=2.0):
        self.x = -70  # Initial state estimate (RSSI starting point)
        self.P = 1.0   # Initial estimate uncertainty
        self.Q = process_variance  # Process variance
        self.R = measurement_variance  # Measurement variance
    
    def update(self, measurement):
        # Prediction step
        self.P += self.Q
        
        # Update step
        K = self.P / (self.P + self.R)  # Kalman Gain
        self.x += K * (measurement - self.x)
        self.P *= (1 - K)
        return self.x

# Initialize Kalman Filters for each beacon
kalman_filters = {}

def kalman_filter_rssi(mac, rssi):
    if mac not in kalman_filters:
        kalman_filters[mac] = KalmanFilter()
    return kalman_filters[mac].update(rssi)

# RSSI to Distance Conversion Function (🔹 Add Here)
def rssi_to_distance(rssi, A=-59, n=2.0):
    """Converts RSSI to estimated distance using the log-distance path loss model."""
    return 10 ** ((A - rssi) / (10 * n))

# Fetch Latest Raw RSSI Values
def fetch_raw_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, ap_id, mac, rssi FROM ble_rssi ORDER BY timestamp DESC LIMIT 50")
    data = cursor.fetchall()
    conn.close()
    return data  # [(id, timestamp, ap_id, mac, rssi), ...]

# Store Filtered RSSI Values
def store_filtered_rssi(filtered_data):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    for timestamp, ap_id, mac, filtered_rssi in filtered_data:
        # Check if this timestamp, ap_id, and mac already exist in filtered_rssi
        cursor.execute("""
            SELECT COUNT(*) FROM filtered_rssi 
            WHERE timestamp = ? AND ap_id = ? AND mac = ?
        """, (timestamp, ap_id, mac))
        
        count = cursor.fetchone()[0]
        
        # Only insert if it's a new entry
        if count == 0:
            cursor.execute("""
                INSERT INTO filtered_rssi (timestamp, ap_id, mac, filtered_rssi)
                VALUES (?, ?, ?, ?)
            """, (timestamp, ap_id, mac, filtered_rssi))

    conn.commit()
    conn.close()
    print(f"Stored {len(filtered_data)} new filtered RSSI values in the database.")


# Process RSSI Filtering
def process_rssi():
    raw_data = fetch_raw_rssi()
    if not raw_data:
        print("No new RSSI data to filter.")
        return
    
    filtered_data = []
    for entry in raw_data:
        rssi_id, timestamp, ap_id, mac, rssi = entry
        filtered_rssi = kalman_filter_rssi(mac, rssi)
        filtered_data.append((timestamp, ap_id, mac, filtered_rssi))
    
    store_filtered_rssi(filtered_data)

if __name__ == "__main__":
    while True:
        print("Filtering RSSI values...")
        process_rssi()
        print("RSSI filtering completed. Waiting for next update...")
        time.sleep(5)
