import os
import sqlite3
import pandas as pd

# 1) Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")


# 2) Load database
# Fetch Latest Raw RSSI Values
def fetch_raw_rssi():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get only entries we haven't processed yet
    cursor.execute("""
        SELECT r.id, r.timestamp, r.ap_id, r.mac, r.device_name, r.rssi 
        FROM wifi_rssi r
        LEFT JOIN wifi_filtered_rssi f 
            ON r.timestamp = f.timestamp 
            AND r.ap_id = f.ap_id 
            AND r.mac = f.mac 
            AND r.device_name = f.device_name
        WHERE f.id IS NULL
        ORDER BY r.timestamp DESC
    """)
    
    data = cursor.fetchall()
    conn.close()
    return data  # [(id, timestamp, ap_id, mac, rssi), ...]

all_raw_rssi = fetch_raw_rssi()
# 3 Sort the devices based on the metres used
ONE_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-XinYi" # change this to the m5stick device's name used to test 
TWO_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-Alicia" # change this to the m5stick device's name used to test 
FOUR_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-KeeShen" # change this to the m5stick device's name used to test 
SIX_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-Enthong" # change this to the m5stick device's name used to test 

# Optional: Define column names
columns = ['ID', 'TIMESTAMP', 'AP_ID', 'MAC', 'DEVICE_NAME', 'RSSI']

# Create the DataFrame
df = pd.DataFrame(all_raw_rssi, columns=columns)
print(df)

