import os
import sqlite3
from scipy.optimize import least_squares
import numpy as np
from rssi_filter import rssi_to_distance  # Import RSSI to Distance function
import time

# SQLite Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
DATABASE = os.path.join(BASE_DIR, "../BLE_only/positioning.db")  # Adjust for correct relative path

# AP Coordinates
AP_COORDINATES = {
    "AP_0": (0, 0),  # Need change AP name to same as the name in DB!!
    "AP_1": (342, 0),
    "AP_2": (0, 384)
}

# Ensure Position Table Exists
def create_position_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estimated_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            x REAL,
            y REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Fetch Latest Filtered RSSI Values Synchronized by Timestamp
def fetch_latest_filtered_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Find the most recent timestamp where at least 3 APs have data
    cursor.execute("""
        SELECT timestamp FROM filtered_rssi 
        GROUP BY timestamp 
        HAVING COUNT(DISTINCT ap_id) >= 3 
        ORDER BY timestamp DESC 
        LIMIT 1
    """)
    latest_timestamp = cursor.fetchone()
    
    if not latest_timestamp:
        conn.close()
        return {}
    
    latest_timestamp = latest_timestamp[0]
    
    # Fetch Filtered RSSI readings from that timestamp
    cursor.execute("SELECT ap_id, mac, filtered_rssi FROM filtered_rssi WHERE timestamp = ?", (latest_timestamp,))
    data = cursor.fetchall()
    conn.close()
    
    rssi_data = {}
    for ap_id, mac, rssi in data:
        if mac not in rssi_data:
            rssi_data[mac] = {}
        rssi_data[mac][ap_id] = rssi
    
    return rssi_data  # {mac: {ap_id: filtered_rssi}}

# Trilateration Function
def trilateration(ap_positions, distances):
    def equations(variables, anchors, distances):
        x, y = variables
        return [(x - anchors[i][0]) ** 2 + (y - anchors[i][1]) ** 2 - distances[i] ** 2 for i in range(len(anchors))]
    
    if len(ap_positions) < 3:
        print("Not enough APs for accurate trilateration (need at least 3). Using closest AP position instead.")
        return ap_positions[0]  # Default to closest AP if trilateration is not possible

    initial_guess = (0, 0)
    result = least_squares(equations, initial_guess, args=(ap_positions, distances))
    return result.x  # Estimated (x, y)

# Estimate Positions
def estimate_positions():
    rssi_data = fetch_latest_filtered_rssi()
    estimated_positions = {}
    
    for mac, ap_rssi in rssi_data.items():
        ap_positions = []
        distances = []
        
        for ap_id, rssi in ap_rssi.items():
            if ap_id in AP_COORDINATES:
                distance = rssi_to_distance(rssi)
                ap_positions.append(AP_COORDINATES[ap_id])
                distances.append(distance)
        
        if len(ap_positions) >= 3:
            estimated_x, estimated_y = trilateration(ap_positions, distances)
            estimated_positions[mac] = (estimated_x, estimated_y)
            print(f"Estimated Position: MAC={mac}, X={estimated_x:.2f}, Y={estimated_y:.2f}")
        else:
            print(f"Not enough APs to estimate position for MAC: {mac}")
    
    return estimated_positions

# Store Estimated Positions in Database
def store_positions(positions):
    if not positions:
        print("No estimated positions to store.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    for mac, (x, y) in positions.items():
        # Check if an entry for this MAC address and timestamp already exists
        cursor.execute("""
            SELECT COUNT(*) FROM estimated_positions 
            WHERE mac = ? AND timestamp = (SELECT MAX(timestamp) FROM estimated_positions WHERE mac = ?)
        """, (mac, mac))
        
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert new position if no existing entry for this timestamp
            cursor.execute("""
                INSERT INTO estimated_positions (mac, x, y, timestamp) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (mac, x, y))
            print(f"Inserted new position: MAC={mac}, X={x:.2f}, Y={y:.2f}")
        else:
            # Optional: Update the latest record instead of inserting a new one
            cursor.execute("""
                UPDATE estimated_positions 
                SET x = ?, y = ?, timestamp = CURRENT_TIMESTAMP 
                WHERE mac = ? AND timestamp = (SELECT MAX(timestamp) FROM estimated_positions WHERE mac = ?)
            """, (x, y, mac, mac))
            print(f"Updated existing position: MAC={mac}, X={x:.2f}, Y={y:.2f}")

    conn.commit()
    conn.close()
    print(f"Database updated with latest estimated positions.")


if __name__ == "__main__":
    create_position_table()
    while True:
        print("Estimating positions...")
        estimated_positions = estimate_positions()
        store_positions(estimated_positions)
        print("Positions updated. Waiting for next update...")
        time.sleep(5)
