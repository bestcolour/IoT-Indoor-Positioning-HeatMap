import sqlite3
import os
import argparse

# List of paths to your positioning.db files
DB_PATHS_MAP = {
    "wifi": "../Wifi_only/positioning.db",
    "ble": "../BLE_only/positioning.db",
    "hybrid": "../BLE+Wifi/positioning.db"
}

# Define ground truth data for each mode
GROUND_TRUTH_MAP = {
    "wifi": [
        ('M5StickCPlus-Alicia', 1.24, 1.24), # Alicia
        ('M5StickCPlus-KeeShen', 2.48, 4.03), # KeeShen
        ('M5StickCPlus-Enthong', 1.24, 6.82), # En Thong
        ('M5StickCPlus-XinYi', 4.34, 0.62), # Xin Yi
        ('M5StickCPlus-Pierre', 4.34, 7.44), # Pierre
    ],
    "ble": [
        ('M5Stick_BLE_Alicia', 1.24, 1.24),
        ('M5Stick_BLE_KeeShen', 2.48, 4.03),
        ('M5Stick_BLE_EnThong', 1.24, 6.82),
        ('M5Stick_BLE_XinYi', 4.34, 0.62),
        ('M5Stick_BLE_Pierre', 4.34, 7.44),
    ],
    "hybrid": [
        ('M5_Alicia', 1.24, 1.24),
        ('M5_KeeShen', 2.48, 4.03),
        ('M5_EnThong', 1.24, 6.82),
        ('M5_XinYi', 4.34, 0.62),
        ('M5_Pierre', 4.34, 7.44),
    ]
}

def insert_ground_truth(db_path, ground_truth):
    if not os.path.exists(db_path):
        print(f"Skipped: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ground_truth_positions (
            device_name TEXT PRIMARY KEY,
            x REAL,
            y REAL
        );
        """)

        # Clear old values (optional, safe if re-running)
        cursor.execute("DELETE FROM ground_truth_positions")

        # Insert ground truth
        cursor.executemany(
            "INSERT INTO ground_truth_positions (device_name, x, y) VALUES (?, ?, ?)",
            ground_truth
        )

        conn.commit()
        print(f"Inserted ground truth into: {db_path}")
    except Exception as e:
        print(f"Error in {db_path}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert ground truth data based on mode.")
    parser.add_argument("mode", choices=["wifi", "ble", "hybrid"], help="Specify the mode (wifi, ble, or hybrid)")
    args = parser.parse_args()

    mode = args.mode
    insert_ground_truth(DB_PATHS_MAP[mode], GROUND_TRUTH_MAP[mode])
