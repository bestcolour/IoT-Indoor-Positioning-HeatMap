import paho.mqtt.client as mqtt
import json
import time
import sqlite3

# MQTT Config
MQTT_BROKER = "192.168.33.148"
MQTT_PORT = 1883
MQTT_TOPIC = "ble/rssi"
MQTT_USERNAME = "team19"
MQTT_PASSWORD = "test123"

# Database SQLite
DATABASE = "positioning.db"
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()

# Cleanup: Remove all rows from relevant tables on start
try:
    tables_to_clear = ["ble_rssi", "estimated_positions", "filtered_rssi"]
    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
    conn.commit()
    print("Cleared ble_rssi, estimated_positions, and filtered_rssi tables.")
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

        receive_time = time.time()  # Timestamp when message is received
        send_time = float(data.get("timestamp", receive_time))  # Timestamp from publisher
        latency = receive_time - send_time
        print(f"Latency: {latency:.3f} seconds")

        if "mac_address" in data and "device_name" in data and "rssi" in data:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            ap_id = data.get("ap_id", "Unknown")
            mac = data["mac_address"]
            device_name = data["device_name"]
            rssi = int(data["rssi"])

            cursor.execute(
                "INSERT INTO ble_rssi (timestamp, ap_id, mac, device_name, rssi, latency) VALUES (?, ?, ?, ?, ?, ?)",
                (time.strftime("%Y-%m-%d %H:%M:%S"), ap_id, mac, device_name, rssi, latency)
            )
            conn.commit()
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
