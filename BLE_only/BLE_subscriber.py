import paho.mqtt.client as mqtt
import json
import time
# import sqlite3
from .BLE_database_helper import clear_table,insert_table,assert_setup_tables

# MQTT Config
MQTT_BROKER = "192.168.33.148"
MQTT_PORT = 1883
MQTT_TOPIC = "ble/rssi"
MQTT_USERNAME = "team19"
MQTT_PASSWORD = "test123"

# Database SQLite
# DATABASE = "positioning.db"
# conn = sqlite3.connect(DATABASE, check_same_thread=False)
assert_setup_tables()

# Cleanup: Remove all rows from relevant tables on start
try:
    tables_to_clear = ["ble_rssi", "ble_estimated_positions", "ble_filtered_rssi"]
    if(clear_table(table_names=tables_to_clear)):
        print(f"Cleared {tables_to_clear}.")
        
    # for table in tables_to_clear:
    #     cursor.execute(text(f"DELETE FROM {table}"))
    #     cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
    # conn.commit()
except Exception as e:
    print(f"Failed to clear tables: {e}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())  # Convert JSON to dictionary
        print("Received MQTT Data:", data)  # Debugging line

        if "mac_address" in data and "device_name" in data and "rssi" in data:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            ap_id = data.get("ap_id", "Unknown")
            mac = data["mac_address"]
            device_name = data["device_name"]
            rssi = int(data["rssi"])

            insert_table(timestamp=timestamp,ap_id=ap_id,mac=mac,device_name=device_name,rssi=rssi)
            print(f"Data Stored: {timestamp} | AP: {ap_id} | MAC: {mac} | Device: {device_name} | RSSI: {rssi} dBm")
        else:
            print("Warning: Unexpected MQTT message format!")

    except json.JSONDecodeError:
        print("Error: Received non-JSON data!")

# Start MQTT Client
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start listening for messages
client.loop_forever()
