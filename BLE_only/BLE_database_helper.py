from db.db_connection import connection
from sqlalchemy import text

# Get the engine object from the connection module to interact with the database
engine = connection.engine

# Function to insert a new row of data into the 'ble_rssi' table.
# Parameters:
#   - timestamp (str): The timestamp when the data was collected.
#   - ap_id (str): The access point ID associated with the data.
#   - mac (str): The MAC address of the device.
#   - device_name (str): The name of the device.
#   - rssi (int): The Received Signal Strength Indicator value for the device.
def insert_table(timestamp: str, ap_id: str, mac: str, device_name: str, rssi: int):
    try:
        with engine.connect() as conn:
            # Execute an SQL statement to insert data into the 'ble_rssi' table
            conn.execute(
                text(
                    """
                    INSERT INTO ble_rssi (timestamp, ap_id, mac, device_name, rssi) 
                    VALUES (:timestamp, :ap_id, :mac, :device_name, :rssi)
                    """
                ),
                {
                    "timestamp": timestamp,
                    "ap_id": ap_id,
                    "mac": mac,
                    "device_name": device_name,
                    "rssi": rssi,
                }
            )
            conn.commit()

    except Exception as e:
        print(f"Error occurred while inserting into the database: {e}")

# Function to clear data from specified tables in the database.
# Parameters:
#   - table_names (list): A list of table names that should have their contents deleted.
# Returns:
#   - bool: True if the table clearing was successful, False otherwise.
def clear_table(table_names: list) -> bool:
    try:
        # Test the connection by executing a simple query
        with engine.connect() as conn:
            for table in table_names:
                # Execute a DELETE statement to remove all records from the given table
                conn.execute(text(f"DELETE FROM {table}"))
                # Optionally clear auto-increment counter if needed (commented out)
                # conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error occurred while clearing the database tables of {table_names}: {e}")
        return False

# Function to check if the setup of necessary tables is complete.
# It creates the 'ble_rssi' table if it doesn't already exist.
def assert_setup_tables():
    try:
        with engine.connect() as conn:
            # Create the 'ble_rssi' table for raw RSSI data if it doesn't exist
            conn.execute(text(
                """
           CREATE TABLE IF NOT EXISTS ble_rssi (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                ap_id VARCHAR(255) DEFAULT 'Unknown',  -- Default value for access point ID
                mac TEXT NOT NULL,                    -- MAC address cannot be NULL
                device_name TEXT NOT NULL,            -- Device name cannot be NULL
                rssi INT NOT NULL                     -- RSSI value cannot be NULL
            )
            """
            ))
            conn.commit()
                
    except Exception as e:
        print(f"Error occurred while connecting to the database: {e}")
