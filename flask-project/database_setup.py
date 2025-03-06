import sqlite3

# Create or connect to the database
conn = sqlite3.connect("positioning.db")
cursor = conn.cursor()

# Create table for raw RSSI data
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ble_rssi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        rssi INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create table for filtered RSSI data (Kalman/Moving Average)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS filtered_rssi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        filtered_rssi INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create table for estimated positions
cursor.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Save changes and close the connection
conn.commit()
conn.close()

print("Database setup complete! Tables created successfully.")