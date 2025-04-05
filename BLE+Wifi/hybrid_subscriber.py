import paho.mqtt.client as mqtt
import json
import time
import sqlite3

# MQTT Config
MQTT_BROKER = "192.168.33.148"
MQTT_PORT = 1883
MQTT_TOPICS = [("wifi/rssi", 0), ("ble/rssi", 0)]
MQTT_USERNAME = "team19"
MQTT_PASSWORD = "test123"

# SQLite DB
DATABASE = "positioning.db"
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()

# === Ensure Tables Exist ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ap_id TEXT,
    mac TEXT,
    device_name TEXT,
    rssi INTEGER,
    latency REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ble_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ap_id TEXT,
    mac TEXT,
    device_name TEXT,
    rssi INTEGER,
    latency REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_estimated_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT,
    x REAL,
    y REAL,
    timestamp TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ble_estimated_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT,
    x REAL,
    y REAL,
    timestamp TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS wifi_filtered_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ap_id TEXT,
    mac TEXT,
    device_name TEXT,
    filtered_rssi REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ble_filtered_rssi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ap_id TEXT,
    mac TEXT,
    device_name TEXT,
    filtered_rssi REAL
)
""")

conn.commit()

# === Cleanup: Clear data on startup ===
tables_to_clear = [
    "wifi_rssi", "ble_rssi",
    "wifi_estimated_positions", "ble_estimated_positions",
    "wifi_filtered_rssi", "ble_filtered_rssi"
]

for table in tables_to_clear:
    cursor.execute(f"DELETE FROM {table}")
    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")  # Reset autoincrement
conn.commit()
print("Cleared all tables on startup.")

# === MQTT Callbacks ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPICS)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        topic = msg.topic

        receive_time = time.time()
        send_time = float(data.get("timestamp_epoch", receive_time))
        latency = receive_time - send_time

        if "mac_address" in data and "device_name" in data and "rssi" in data:
            timestamp = data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
            ap_id = data.get("ap_id", "Unknown")
            mac = data["mac_address"]
            device_name = data["device_name"]
            rssi = int(data["rssi"])

            if topic == "wifi/rssi":
                table = "wifi_rssi"
            elif topic == "ble/rssi":
                table = "ble_rssi"
            else:
                print(f"Unknown topic: {topic}")
                return

            cursor.execute(
                f"""INSERT INTO {table} (timestamp, ap_id, mac, device_name, rssi, latency)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (timestamp, ap_id, mac, device_name, rssi, latency)
            )
            conn.commit()
            print(f"Stored [{table}]: {timestamp} | AP: {ap_id} | MAC: {mac} | Device: {device_name} | RSSI: {rssi} | Latency: {latency:.3f}s")
        else:
            print("Missing fields in MQTT payload.")

    except json.JSONDecodeError:
        print("JSON Decode Error!")
    except Exception as e:
        print(f"Unexpected Error: {e}")

# === Start MQTT Client ===
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
