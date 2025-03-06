from filterpy.kalman import KalmanFilter
import numpy as np
import sqlite3
import time

DATABASE = "BLE_only/positioning.db"  # Ensure correct path

def kalman_filter_rssi(rssi_value, prev_value=-70):
    """Applies a Kalman filter to a single RSSI value."""
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = np.array([[prev_value]])  # Use previous RSSI as initial value
    kf.F = np.array([[1]])  # State transition matrix
    kf.H = np.array([[1]])  # Measurement function
    kf.P *= 1000  # Initial covariance matrix
    kf.R = np.array([[10]])  # Measurement noise
    kf.Q = np.array([[1]])  # Process noise

    kf.predict()
    kf.update([rssi_value])

    return kf.x[0, 0]  # Return filtered RSSI

def moving_average_filter(rssi_values, window_size=3):
    """Applies a moving average filter to RSSI values."""
    if len(rssi_values) < window_size:
        return np.mean(rssi_values)  # Return mean if not enough values
    return np.convolve(rssi_values, np.ones(window_size)/window_size, mode='valid')[-1]

def rssi_to_distance(rssi, A=-59, n=2.0):
    """Converts RSSI to estimated distance using the log-distance path loss model."""
    return 10 ** ((A - rssi) / (10 * n))

def fetch_and_filter_rssi():
    """Fetches latest RSSI values from database, filters them, and stores in filtered_rssi table."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch latest RSSI readings
    cursor.execute("SELECT id, mac, rssi FROM ble_rssi ORDER BY timestamp DESC LIMIT 10")
    rssi_data = cursor.fetchall()

    for entry in rssi_data:
        rssi_id, mac, rssi = entry
        filtered_rssi = kalman_filter_rssi(rssi)  # Apply Kalman filtering

        # Store filtered RSSI into the database
        cursor.execute("INSERT INTO filtered_rssi (mac, filtered_rssi) VALUES (?, ?)", (mac, int(filtered_rssi)))

    conn.commit()
    conn.close()
    print("Filtered RSSI values stored in the database.")

if __name__ == "__main__":
    while True:
        fetch_and_filter_rssi()
        print("Filtered RSSI stored. Waiting for next update...")
        time.sleep(5) # Wait 5 seconds before fetching new RSSI data
