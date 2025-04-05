import os
import sqlite3
import pandas as pd
import numpy as np


# read more: https://www.gaussianwaves.com/2013/09/log-distance-path-loss-or-log-normal-shadowing-model/
# 1) Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "positioning.db")

# Optional: Define column names
COLUMN_ID = 'ID'
COLUMN_TIMESTAMP = 'TIMESTAMP'
COLUMN_AP_ID = 'AP_ID'
COLUMN_MAC = 'MAC'
COLUMN_DEVICE_NAME = 'DEVICE_NAME'
COLUMN_RSSI = 'RSSI'

columns = [COLUMN_ID, COLUMN_TIMESTAMP, COLUMN_AP_ID, COLUMN_MAC, COLUMN_DEVICE_NAME, COLUMN_RSSI]

#ks - 1, alicia - 4th , xy - 2nd , eth - 3rd
# Sort the devices based on the metres used
ONE_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-KeeShen" # change this to the m5stick device's name used to test 
TWO_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-XinYi" # change this to the m5stick device's name used to test 
FOUR_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-Alicia" # change this to the m5stick device's name used to test 
SIX_METRE_TESTING_M5_DEVICE_NAME = "M5StickCPlus-Enthong" # change this to the m5stick device's name used to test 

# store all intervals except for 1 metre in a list as 1 metre readings will be used to calculate A
DISTANCE_INTERVALS = [ONE_METRE_TESTING_M5_DEVICE_NAME,TWO_METRE_TESTING_M5_DEVICE_NAME,FOUR_METRE_TESTING_M5_DEVICE_NAME,SIX_METRE_TESTING_M5_DEVICE_NAME]

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

device_to_dist_dict:dict = {
    ONE_METRE_TESTING_M5_DEVICE_NAME:1
    ,
    TWO_METRE_TESTING_M5_DEVICE_NAME:2
    ,
    FOUR_METRE_TESTING_M5_DEVICE_NAME:4
    ,
    SIX_METRE_TESTING_M5_DEVICE_NAME:6
}

def calculate_n_for_measurements_from_df(df, A):
    """
    Calculates the path loss exponent (n) for each distance using the log-distance path loss model.
    
    Parameters:
    - df: A pandas DataFrame containing 'distance' (in meters) and 'rssi' (in dBm).
    - A: The reference RSSI at 1 meter (in dBm).
    
    Returns:
    - n_values: List of calculated n values for each distance (except 1 meter).
    - average_n: The average of all calculated n values.
    """
    n_values = []

    # Loop through the rows, skipping the first row (distance = 1 meter)
    for _, row in df.iterrows():
        distance = device_to_dist_dict.get(row[COLUMN_DEVICE_NAME])
        rssi = row[COLUMN_RSSI]
        
        if distance == 1:  # Skip the 1-meter point as n = 0 at 1 meter
            continue
        
        # Calculate n using the log-distance path loss model
        n = (A - rssi) / (10 * np.log10(distance))
        n_values.append(n)
    
    # Calculate the average n
    average_n = np.mean(n_values) if n_values else 0  # Avoid division by zero if no values
    
    return n_values, average_n



def calculate_A_from_readings(rssi_readings):
    """
    Calculates the reference RSSI at 1 meter (A) by averaging multiple RSSI readings.
    
    Parameters:
    - rssi_readings: A list or numpy array of RSSI values measured at 1 meter (in dBm).
    
    Returns:
    - A: The estimated reference RSSI at 1 meter (in dBm).
    """
    A = np.mean(rssi_readings)
    return A


all_raw_rssi = fetch_raw_rssi()
# 3 Create the DataFrame
df = pd.DataFrame(all_raw_rssi, columns=columns)
print(df)

# Get A's values
condition = df['DEVICE_NAME'] == ONE_METRE_TESTING_M5_DEVICE_NAME
filtered_df = df[condition]
A = calculate_A_from_readings(filtered_df["RSSI"])
print(f"A is {A}")

n_values = []
# Create a boolean Series indicating which rows satisfy the condition
for interval in DISTANCE_INTERVALS:
    # skip 1 m testings
    if(interval == ONE_METRE_TESTING_M5_DEVICE_NAME):
        continue

    # get the condition of device name being matching the same string as our interval
    condition = df[COLUMN_DEVICE_NAME] == interval

    # Use the boolean Series to select the rows
    filtered_df = df[condition]

    _, avg_n = calculate_n_for_measurements_from_df(df=filtered_df,A=A)
    n_values.append(avg_n) # average n for this specific distance is appended to list
    pass

average_n_value = np.mean(n_values) # average n value for all distances 

print(f"List of n values {n_values}\n average_n_value: {average_n_value}")