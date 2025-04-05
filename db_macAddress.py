import sqlite3
import os

# List of paths to your positioning.db files
DB_PATHS = [
    "BLE_only/positioning.db",
    "Wifi_only/positioning.db",
    # "Hybrid/positioning.db"
]

# Ground truth data (MAC, x, y)
# GROUND_TRUTH = [
#     ('4c:75:25:cb:86:8e', 1.24, 1.24), # Alicia
#     ('ac:0b:fb:6f:9d:fe', 2.48, 4.03), # KeeShen
#     ('4c:75:25:cb:8e:36', 1.24, 6.82), # En Thong
#     ('4c:75:25:cb:83:26', 4.34, 0.62), # Xin Yi
#     ('4c:75:25:cb:8e:32', 4.34, 7.44), # Pierre
# ]

GROUND_TRUTH = [
    ('M5StickCPlus-Alicia', 1.24, 1.24), # Alicia
    ('M5StickCPlus-KeeShen', 2.48, 4.03), # KeeShen
    ('M5StickCPlus-Enthong', 1.24, 6.82), # En Thong
    ('M5StickCPlus-XinYi', 4.34, 0.62), # Xin Yi
    ('M5StickCPlus-Pierre', 4.34, 7.44), # Pierre
]

def insert_ground_truth(db_path):
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
            GROUND_TRUTH
        )

        conn.commit()
        print(f"Inserted ground truth into: {db_path}")
    except Exception as e:
        print(f"Error in {db_path}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    for path in DB_PATHS:
        insert_ground_truth(path)
