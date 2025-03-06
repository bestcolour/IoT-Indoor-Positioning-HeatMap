import paho.mqtt.client as mqtt
import json
import csv
import time

# MQTT Config
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC = "ble/rssi"
MQTT_USERNAME = "team19"
MQTT_PASSWORD = "test123"

# CSV File
csv_filename = "ble_rssi_log.csv"

# Open CSV file and write headers (only if file is empty)
try:
    with open(csv_filename, "x", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "MAC Address", "Device Name", "RSSI (dBm)"])
except FileExistsError:
    pass  # If file already exists, do nothing

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

        # Ensure the message contains the expected fields
        if "mac_address" in data and "device_name" in data and "rssi" in data:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # Write data to CSV file
            with open(csv_filename, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, data["mac_address"], data["device_name"], data["rssi"]])

            print(f"Data Stored: {timestamp} | MAC: {data['mac_address']} | Device: {data['device_name']} | RSSI: {data['rssi']} dBm")
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
