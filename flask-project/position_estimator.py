import os
import sqlite3
import numpy as np
from scipy.optimize import least_squares
from rssi_filter import rssi_to_distance
import time

# SQLite Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "../BLE_only/positioning.db")

# AP Coordinates
AP_COORDINATES = {
    "pierre": (0, 0),
    "keshleepi": (342, 0),
    "enthong": (0, 384)
}

# Ensure database tables exist
def create_position_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create estimated_positions table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estimated_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            x REAL,
            y REAL,
            timestamp DATETIME,
            UNIQUE(mac, timestamp)
        )
    """)
    
    conn.commit()
    conn.close()

# Fetch Latest Filtered RSSI Values Synchronized by Timestamp
def fetch_filtered_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch all timestamps where at least 3 APs have data
    cursor.execute("""
        SELECT DISTINCT timestamp FROM filtered_rssi 
        WHERE timestamp IN (
            SELECT timestamp FROM filtered_rssi 
            GROUP BY timestamp 
            HAVING COUNT(DISTINCT ap_id) >= 3
        )
        ORDER BY timestamp ASC
    """)
    timestamps = [row[0] for row in cursor.fetchall()]

    if not timestamps:
        conn.close()
        return {}

    rssi_data = {}

    for timestamp in timestamps:
        cursor.execute("""
            SELECT ap_id, mac, filtered_rssi FROM filtered_rssi WHERE timestamp = ?
        """, (timestamp,))
        data = cursor.fetchall()

        for ap_id, mac, rssi in data:
            if mac not in rssi_data:
                rssi_data[mac] = {}
            if timestamp not in rssi_data[mac]:
                rssi_data[mac][timestamp] = {}
            rssi_data[mac][timestamp][ap_id] = rssi

    conn.close()
    return rssi_data  # {mac: {timestamp: {ap_id: filtered_rssi}}}

# Improved Trilateration Function using least_squares optimization
def improved_trilateration(ap_positions, distances):
    # Convert inputs to numpy arrays
    points = np.array(ap_positions)
    dists = np.array(distances)
    
    # Weights based on distance reliability (closer APs get higher weight)
    weights = 1.0 / (dists + 0.1)  # Adding 0.1 to avoid division by zero
    
    # Debug prints
    print("\n**Improved Trilateration Debug Info**")
    print("AP Positions:", ap_positions)
    print("Distances:", distances)
    print("Weights:", weights)
    
    # Define the residual function for least squares optimization
    def residuals(point):
        return weights * (np.sqrt(np.sum((points - point)**2, axis=1)) - dists)
    
    try:
        # Initial guess (centroid of AP positions)
        initial_guess = np.mean(points, axis=0)
        print("Initial position guess:", initial_guess)
        
        # Solve using Levenberg-Marquardt algorithm
        result = least_squares(residuals, initial_guess, method='lm')
        
        if result.success:
            print("Optimization succeeded with cost:", result.cost)
            return result.x
        else:
            print("Trilateration optimization failed with status:", result.status)
            return None, None
    except Exception as e:
        print(f"Error in improved trilateration: {e}")
        return None, None

# Legacy weighted trilateration function as fallback
def weighted_trilateration(ap_positions, distances):
    A = []
    b = []
    weights = []

    for i in range(1, len(ap_positions)):
        x0, y0 = ap_positions[0]
        xi, yi = ap_positions[i]
        di_sq = distances[i] ** 2 - distances[0] ** 2
        A.append([2 * (xi - x0), 2 * (yi - y0)])
        b.append(di_sq - (xi**2 + yi**2 - x0**2 - y0**2))

        # Weighting: Closer APs get higher weight
        weight = 1 / (distances[i] + 1e-6)
        weights.append(weight)

    A = np.array(A)
    b = np.array(b)
    W = np.diag(weights)  # Weight matrix

    # Debugging Prints 
    print("\n**Weighted Trilateration Debug Info**")
    print("AP Positions:", ap_positions)
    print("Distances:", distances)
    print("Distance Matrix (A):\n", A)
    print("Observation Vector (b):\n", b)
    print("Weight Matrix (W):\n", W)

    # Solve Weighted Least Squares: (A^T W A) x = A^T W b
    try:
        x = np.linalg.inv(A.T @ W @ A) @ A.T @ W @ b
        return x  # Estimated (x, y)
    except np.linalg.LinAlgError:
        print("Weighted Trilateration Failed: Singular Matrix")
        return None, None

# Estimate Positions
def estimate_positions():
    rssi_data = fetch_filtered_rssi()
    estimated_positions = {}

    for mac, timestamps in rssi_data.items():
        for timestamp, ap_rssi in timestamps.items():
            ap_positions = []
            distances = []

            for ap_id, rssi in ap_rssi.items():
                if ap_id in AP_COORDINATES:
                    distance = rssi_to_distance(rssi)
                    ap_positions.append(AP_COORDINATES[ap_id])
                    distances.append(distance)
                    print(f"📡 RSSI: {rssi:.2f} dBm → Distance: {distance:.2f}m (AP: {ap_id})")

            if len(ap_positions) >= 3:
                print(f"🔹 Trilateration Inputs for MAC={mac} at {timestamp}:")
                print(f"   AP Positions: {ap_positions}")
                print(f"   Distances: {distances}")

                # Try improved trilateration first
                try:
                    result = improved_trilateration(ap_positions, distances)
                    if result is not None and len(result) == 2:
                        estimated_x, estimated_y = result
                    else:
                        # Fall back to legacy trilateration
                        estimated_x, estimated_y = weighted_trilateration(ap_positions, distances)
                except Exception as e:
                    print(f"Error in improved trilateration: {e}")
                    # Fall back to legacy trilateration
                    estimated_x, estimated_y = weighted_trilateration(ap_positions, distances)
                
                if estimated_x is not None and estimated_y is not None:
                    estimated_positions[(mac, timestamp)] = (float(estimated_x), float(estimated_y))
                    print(f"✅ Estimated Position: MAC={mac}, X={estimated_x:.2f}, Y={estimated_y:.2f} at {timestamp}")
                else:
                    print(f"❌ Trilateration failed for MAC={mac} at {timestamp}")
            else:
                print(f"⚠️ Not enough APs to estimate position for MAC: {mac} at {timestamp}")

    return estimated_positions

# Store Estimated Positions in Database
def store_positions(positions):
    if not positions:
        print("No estimated positions to store.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for (mac, timestamp), (x, y) in positions.items():
        # Use INSERT OR REPLACE to handle duplicates more efficiently
        cursor.execute("""
            INSERT OR REPLACE INTO estimated_positions (mac, x, y, timestamp) 
            VALUES (?, ?, ?, ?)
        """, (mac, x, y, timestamp))
        print(f"Stored position: MAC={mac}, X={x:.2f}, Y={y:.2f}, Timestamp={timestamp}")

    conn.commit()
    conn.close()
    print(f"Database updated with {len(positions)} estimated positions.")

if __name__ == "__main__":
    create_position_table()
    try:
        while True:
            print("\n==== Position Estimation Cycle Started ====")
            estimated_positions = estimate_positions()
            store_positions(estimated_positions)
            print("==== Position Estimation Cycle Completed ====")
            print(f"Waiting {5} seconds for next update...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("Position estimator terminated by user.")
    except Exception as e:
        print(f"Error in position estimator: {e}")