import paho.mqtt.client as mqtt
import json
import time
from bluepy.btle import Scanner
import socket

MQTT_BROKER = "192.168.33.64"
MQTT_PORT = 1883
MQTT_TOPIC = "ble/rssi"
MQTT_USER = "team19"
MQTT_PASSWORD = "test123"

TARGET_MACS = ["ac:0b:fb:6f:9d:fe", "4c:75:25:cb:8e:32", "4c:75:25:cb:86:8e", "4c:75:25:cb:8e:36", "4c:75:25:cb:83:26"]
AP_IDENTIFIER = socket.gethostname()

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

scanner = Scanner()

while True:
    devices = scanner.scan(5.0)
    for dev in devices:
        if dev.addr.lower() in TARGET_MACS:
            timestamp_epoch = time.time()
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_epoch))
            device_name = "Unknown"

            for (adtype, desc, value) in dev.getScanData():
                if adtype == 9:
                    device_name = value

            payload = {
                "timestamp": timestamp_str,
                "timestamp_epoch": timestamp_epoch,
                "ap_id": AP_IDENTIFIER,
                "mac_address": dev.addr,
                "device_name": device_name,
                "rssi": dev.rssi
            }

            mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
            print(f"Published BLE: {payload}")
    time.sleep(2)
