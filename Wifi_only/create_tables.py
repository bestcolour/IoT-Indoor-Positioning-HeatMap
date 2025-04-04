import sqlite3

# Connect to the existing database
conn = sqlite3.connect("positioning.db")
cursor = conn.cursor()

# 1. WiFi RSSI Table (raw readings)
cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME,
    ap_id TEXT,
    mac TEXT,
    device_name TEXT,
    rssi INTEGER
)
""")

# 2. WiFi Filtered RSSI Table (e.g., moving average or Kalman output)
cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_filtered_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME,
    ap_id TEXT,
    mac TEXT,
    filtered_rssi REAL
)
""")

# 3. WiFi Estimated Positions Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_estimated_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT,
    x REAL,
    y REAL,
    timestamp DATETIME
)
""")

conn.commit()
conn.close()
print("Tables created successfully.")
