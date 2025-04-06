# Running the scripts
# python calculate_accuracy.py wifi
# python calculate_accuracy.py ble
# python calculate_accuracy.py hybrid

import argparse
import sqlite3
import math
import os

def calculate_accuracy(table_name, db_path, rssi_table):
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        query = f"""
        SELECT e.device_name, e.x, e.y, g.x, g.y, r.latency
        FROM {table_name} e
        JOIN ground_truth_positions g ON e.device_name = g.device_name
        LEFT JOIN (
            SELECT device_name, MIN(latency) AS latency
            FROM {rssi_table}
            WHERE latency >= 0
            GROUP BY device_name
        ) r ON e.device_name = r.device_name
        LIMIT 400
        """
        rows = cursor.execute(query).fetchall()

        errors = []
        latencies = []

        for _, xe, ye, xt, yt, latency in rows:
            errors.append(math.sqrt((xe - xt) ** 2 + (ye - yt) ** 2))
            if latency is not None:
                latencies.append(latency)

        if errors:
            mean_error = sum(errors) / len(errors)
            median_error = sorted(errors)[len(errors) // 2]

            print(f"\n Method: {table_name}")
            print(f"→ Mean Error: {mean_error:.2f} meters")
            print(f"→ Median Error: {median_error:.2f} meters")
            print(f"→ Sample Count: {len(errors)}")

            if latencies:
                mean_latency = sum(latencies) / len(latencies)
                # median_latency = sorted(latencies)[len(latencies) // 2]
                print(f"→ Mean Latency: {mean_latency:.4f} ms")
                # print(f"→ Median Latency: {median_latency:.4f} ms\n")
            else:
                print("→ No latency data found.\n")
        else:
            print("No data available for comparison.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate positioning accuracy.")
    parser.add_argument("mode", choices=["wifi", "ble", "hybrid"], help="Mode to evaluate (wifi, ble, or hybrid)")
    args = parser.parse_args()

    # Default values based on mode
    if args.mode == "wifi":
        db_path = "../Wifi_only/positioning.db"
        table_name = "wifi_estimated_positions"
        rssi_table = "wifi_rssi"
    elif args.mode == "ble":
        db_path = "../BLE_only/positioning.db"
        table_name = "estimated_positions"
        rssi_table = "filtered_rssi"
    elif args.mode == "hybrid":
        db_path = "../BLE+Wifi/positioning.db"
        table_name = "hybrid_estimated_positions"
        rssi_table = "hybrid_filtered_rssi"
    calculate_accuracy(table_name, db_path, rssi_table)