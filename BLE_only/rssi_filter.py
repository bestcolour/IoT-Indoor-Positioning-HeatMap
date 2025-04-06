import sqlite3
import numpy as np
import time
import os

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

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

# Creating necessary tables
def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create ble_rssi table if it doesn't exist (raw data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ble_rssi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ap_id TEXT,
            mac TEXT,
            rssi REAL
        )
    """)

    # Drop and recreate filtered_rssi table
    cursor.execute("DROP TABLE IF EXISTS filtered_rssi")
    print(f"Dropped filtered_rssi table...")
    
    # Create filtered_rssi table if it doesn't exist
    cursor.execute("""
        CREATE TABLE filtered_rssi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            ap_id TEXT,
            mac TEXT,
            device_name TEXT,
            filtered_rssi REAL,
            latency REAL,
            UNIQUE(timestamp, ap_id, mac)
        )
    """)

    
    conn.commit()
    conn.close()

def kalman_filter_rssi(mac, rssi):
    """Apply Kalman filter to smooth RSSI values for a specific MAC address"""
    if mac not in kalman_filters:
        kalman_filters[mac] = KalmanFilter()
    return kalman_filters[mac].update(rssi)

# RSSI to Distance Conversion using Log-Distance Path Loss Model
def rssi_to_distance(rssi, A=-55.525, n=0.73529100890785):
    """
    Converts RSSI to estimated distance using the log-distance path loss model.
    
    Parameters:
    - rssi: Measured RSSI value in dBm
    - A: Reference RSSI at 1 meter distance (calibration parameter)
    - n: Path loss exponent (depends on environment)
    
    Returns:
    - Estimated distance in meters
    """
    return 10 ** ((A - rssi) / (10 * n))

# Calibrate RSSI model parameters using known measurements
def calibrate_rssi_model(known_distance_measurements):
    """
    Calibrate the RSSI-to-distance model parameters
    
    Parameters:
    - known_distance_measurements: List of tuples [(rssi_value, known_distance), ...]
    
    Returns:
    - A0: Calibrated reference RSSI at 1 meter
    - n: Calibrated path loss exponent
    """
    if not known_distance_measurements or len(known_distance_measurements) < 2:
        print("Not enough calibration data points")
        return -59, 3.0  # Default values
    
    # Extract data points
    rssi_values = np.array([m[0] for m in known_distance_measurements])
    distances = np.array([m[1] for m in known_distance_measurements])
    
    # Convert to log scale for linear regression
    log_distances = np.log10(distances)
    
    # Linear regression to find parameters
    A = np.vstack([np.ones(len(rssi_values)), rssi_values]).T
    try:
        n, A0 = np.linalg.lstsq(A, -10 * log_distances, rcond=None)[0]
        print(f"Calibrated parameters: A0={A0}, n={n/10}")
        return A0, n / 10
    except Exception as e:
        print(f"Calibration error: {e}")
        return -59, 3.0  # Default values

# Fetch Latest Raw RSSI Values
def fetch_raw_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get only entries we haven't processed yet
    cursor.execute("""
        SELECT r.id, r.timestamp, r.ap_id, r.mac, r.device_name, r.rssi, r.latency
        FROM ble_rssi r
        LEFT JOIN filtered_rssi f ON r.timestamp = f.timestamp AND r.ap_id = f.ap_id AND r.mac = f.mac
        WHERE f.id IS NULL
        ORDER BY r.timestamp DESC
    """)

    
    data = cursor.fetchall()
    conn.close()
    return data  # [(id, timestamp, ap_id, mac, rssi), ...]

# Store Filtered RSSI Values with batch processing
def batch_store_filtered_rssi(filtered_data):
    if not filtered_data:
        return 0
        
    conn = sqlite3.connect(DATABASE)
    
    # Use executemany for batch inserts
    conn.executemany("""
        INSERT OR IGNORE INTO filtered_rssi (timestamp, ap_id, mac, device_name, filtered_rssi, latency)
        VALUES (?, ?, ?, ?, ?, ?)
    """, filtered_data)

    
    rows_affected = conn.total_changes
    conn.commit()
    conn.close()
    
    return rows_affected

# Process RSSI Filtering
def process_rssi():
    raw_data = fetch_raw_rssi()
    if not raw_data:
        print("No new RSSI data to filter.")
        return 0
    
    filtered_data = []
    for entry in raw_data:
        rssi_id, timestamp, ap_id, mac, device_name, rssi, latency = entry
        filtered_rssi = kalman_filter_rssi(mac, rssi)
        filtered_data.append((timestamp, ap_id, mac, device_name, filtered_rssi, latency))

    
    rows_stored = batch_store_filtered_rssi(filtered_data)
    return rows_stored

if __name__ == "__main__":
    create_tables()                   # Create the tables if they don't exist
    rows_stored = process_rssi()     # Fetch & filter new RSSI data
    print(f"Rows stored: {rows_stored}")



