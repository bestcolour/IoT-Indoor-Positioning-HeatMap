import paho.mqtt.client as mqtt
import sqlite3
import json

# MQTT Config
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = "ble/rssi"
MQTT_USERNAME = "team19"
MQTT_PASSWORD = "test123"

# Connect to SQLite database
conn = sqlite3.connect("positioning.db", check_same_thread=False)
cursor = conn.cursor()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    for entry in data["data"]:
        cursor.execute("INSERT INTO ble_rssi (mac, rssi) VALUES (?, ?)", (entry["mac"], entry["rssi"]))
    conn.commit()
    print("RSSI Data Stored")

# Start MQTT Client
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD) 
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

client.loop_forever()