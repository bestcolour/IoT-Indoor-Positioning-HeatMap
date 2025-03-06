# This code will be transferred to the Raspberry Pi 4 to scan for BLE devices and publish the RSSI value to the MQTT broker.
# scp command: scp BLE_scanner.py ksprojectpi@172.20.10.4:/home/ksprojectpi/IoTProject/bluepy/
import paho.mqtt.client as mqtt
import json
import time
from bluepy.btle import Scanner

# MQTT Broker Configuration
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC = "ble/rssi"
MQTT_USER = "team19"  # MQTT username
MQTT_PASSWORD = "test123"  # MQTT password

# Target MAC Address to Filter
TARGET_MAC = "ac:0b:fb:6f:9d:fe"

# Initialize MQTT Client with Authentication
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# BLE Scanner
scanner = Scanner()

while True:
    devices = scanner.scan(5.0)  # Scan for 5 seconds
    for dev in devices:
        if dev.addr.lower() == TARGET_MAC:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            device_name = "Unknown"

            # Try to get device name
            for (adtype, desc, value) in dev.getScanData():
                if adtype == 9:
                    device_name = value

            # Prepare MQTT payload
            payload = {
                "timestamp": timestamp,
                "mac_address": dev.addr,
                "device_name": device_name,
                "rssi": dev.rssi
            }

            # Publish data to MQTT broker with authentication
            mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
            print(f"Published to MQTT: {payload}")

    time.sleep(2)
