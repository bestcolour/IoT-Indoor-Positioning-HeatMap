from db.db_connection import connection
from sqlalchemy import text

engine = connection.engine

def insert_table(timestamp:str,ap_id:str,mac:str,device_name:str,rssi:int):
    try:
        with engine.connect() as conn:
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

# if return true, then clearing of table is successful else false
def clear_table(table_names:list) -> bool:
    try:
        # Test the connection by executing a simple query
        with engine.connect() as conn:
            for table in table_names:
                conn.execute(text(f"DELETE FROM {table}"))
                # conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error occurred while clearing the database tables of {table_names}: {e}")
        return False

def assert_setup_tables():
    try:
        with engine.connect() as conn:
            # Create table for raw RSSI data
            conn.execute(text(
                """
           CREATE TABLE IF NOT EXISTS ble_rssi (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                ap_id VARCHAR(255) DEFAULT 'Unknown',  -- Now using VARCHAR
                mac TEXT NOT NULL,
                device_name TEXT NOT NULL,
                rssi INT NOT NULL
            )

            """
            ))
            conn.commit()
                
    except Exception as e:
        print(f"Error occurred while connecting to the database: {e}")