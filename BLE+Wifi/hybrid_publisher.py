import paho.mqtt.client as mqtt
import json
import time
from bluepy.btle import Scanner
import socket

# MQTT Config
MQTT_BROKER = "keshleepi.local"  # Use hostname
MQTT_PORT = 8883  # TLS port
MQTT_TOPIC = "ble/rssi"
MQTT_USER = "team19"
MQTT_PASSWORD = "test123"

# TLS Certificate Paths
CA_CERT = "certs/ca.crt"
CLIENT_CERT = "certs/client.crt"
CLIENT_KEY = "certs/client.key"

# MAC address to device name mapping
DEVICE_NAME_MAP = {
    "4c:75:25:cb:86:8e": "M5Stick_BLE_Alicia",
    "ac:0b:fb:6f:9d:fe": "M5Stick_BLE_KeeShen",
    "4c:75:25:cb:8e:36": "M5Stick_BLE_EnThong",
    "4c:75:25:cb:83:26": "M5Stick_BLE_XinYi",
    "4c:75:25:cb:8e:32": "M5Stick_BLE_Pierre"
}

TARGET_MACS = list(DEVICE_NAME_MAP.keys())
AP_IDENTIFIER = socket.gethostname()

# Initialize MQTT client with TLS
mqtt_client = mqtt.Client()
mqtt_client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
# Optionally disable hostname check if using IP instead of CN
# mqtt_client.tls_insecure_set(True)

mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# BLE Scanner
scanner = Scanner()

while True:
    devices = scanner.scan(5.0)
    for dev in devices:
        mac = dev.addr.lower()
        if mac in TARGET_MACS:
            timestamp_epoch = time.time()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_epoch))
            device_name = DEVICE_NAME_MAP.get(mac, "Unknown")

            payload = {
                "timestamp": timestamp,
                "timestamp_epoch": timestamp_epoch,
                "ap_id": AP_IDENTIFIER,
                "mac_address": mac,
                "device_name": device_name,
                "rssi": dev.rssi
            }

            mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
            print(f"Published BLE: {payload}")
    time.sleep(2)
