import os
import sqlite3
from scipy.optimize import least_squares
import numpy as np
from rssi_filter import kalman_filter_rssi, moving_average_filter, rssi_to_distance  # Import filtering functions
import time

# SQLite Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
DATABASE = os.path.join(BASE_DIR, "../BLE_only/positioning.db")  # Adjust for correct relative path

def fetch_latest_rssi():
    """
    Fetch the latest RSSI values for each unique MAC address from the database.
    Returns a dictionary {mac: [list of RSSI readings]}.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT mac, rssi FROM ble_rssi ORDER BY timestamp DESC LIMIT 10")  # Fetch the last 10 readings
    data = cursor.fetchall()
    
    conn.close()
    
    rssi_data = {}
    for mac, rssi in data:
        if mac not in rssi_data:
            rssi_data[mac] = []
        rssi_data[mac].append(rssi)
    
    return rssi_data  # Dictionary {mac: [rssi_list]}

def trilateration(anchors, distances):
    """
    Estimates the (x, y) position of a BLE beacon given distances from fixed anchors.
    """
    def equations(variables, anchors, distances):
        x, y = variables
        return [(x - anchors[i][0]) ** 2 + (y - anchors[i][1]) ** 2 - distances[i] ** 2 for i in range(len(anchors))]

    initial_guess = (0, 0)  # Starting guess
    result = least_squares(equations, initial_guess, args=(anchors, distances))
    
    return result.x  # Returns estimated (x, y) position

def estimate_positions():
    """
    Estimates positions of all BLE devices using RSSI filtering and trilateration.
    """
    anchors = [(0, 0), (5, 0), (2.5, 4)]  # Set your anchor positions
    rssi_data = fetch_latest_rssi()
    
    estimated_positions = {}

    for mac, rssi_list in rssi_data.items():
        # Apply RSSI filtering (change to "kalman" if needed)
        filtered_rssi = [moving_average_filter(rssi_list) for _ in range(3)]

        # Convert RSSI to distances
        distances = [rssi_to_distance(rssi) for rssi in filtered_rssi]

        # Estimate position
        position = trilateration(anchors, distances)

        estimated_positions[mac] = position
    
    return estimated_positions

def store_positions(positions):
    """
    Stores estimated positions in the SQLite database.
    """
    if not positions:
        print("No estimated positions to store.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for mac, (x, y) in positions.items():
        cursor.execute("""
            INSERT INTO positions (mac, x, y, timestamp) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (mac, x, y))

    conn.commit()
    conn.close()
    print(f"Stored {len(positions)} estimated positions in the database.")


if __name__ == "__main__":
    while True:
        print("Estimating positions...")
        estimated_positions = estimate_positions()
        store_positions(estimated_positions)
        print("Positions updated. Waiting for next update...")
        time.sleep(5)  # Wait 5 seconds before recalculating positions
