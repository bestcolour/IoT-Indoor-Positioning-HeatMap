#include <M5StickCPlus.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>
#include <BLEServer.h>

const char* ssid = "kys_dont_kys";
const char* password = "killmepls";

const char* mqtt_server = "192.168.33.148";
const int mqtt_port = 1883;
const char* mqtt_user = "team19";
const char* mqtt_password = "test123";
const char* mqtt_topic_wifi = "wifi/rssi";

const char* DEVICE_NAME = "M5StickCPlus-KeeShen";
#define BEACON_UUID "12345678-9012-3456-7890-1234567890AB"

WiFiClient espClient;
PubSubClient client(espClient);

void startBLEBeacon() {
  BLEDevice::init(DEVICE_NAME);
  BLEServer* pServer = BLEDevice::createServer();
  BLEBeacon oBeacon = BLEBeacon();
  oBeacon.setManufacturerId(0x4C00);
  oBeacon.setProximityUUID(BLEUUID(BEACON_UUID));
  oBeacon.setMajor(1);
  oBeacon.setMinor(1);
  BLEAdvertisementData oAdvertisementData;
  std::string strServiceData = "";
  strServiceData += (char)26;
  strServiceData += (char)0xFF;
  strServiceData += oBeacon.getData();
  oAdvertisementData.addData(strServiceData);
  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->setAdvertisementData(oAdvertisementData);
  pAdvertising->start();
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  configTime(0, 0, "time.google.com");
  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    now = time(nullptr);
  }
}

void connectToMQTT() {
  while (!client.connected()) {
    if (!client.connect(DEVICE_NAME, mqtt_user, mqtt_password)) {
      delay(2000);
    }
  }
}

String getTimestamp() {
  time_t now = time(nullptr);
  struct tm* t = localtime(&now);
  char timestamp[25];
  sprintf(timestamp, "%04d-%02d-%02d %02d:%02d:%02d",
          t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
          t->tm_hour, t->tm_min, t->tm_sec);
  return String(timestamp);
}

void setup() {
  M5.begin();
  M5.Lcd.setRotation(3);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(1);
  connectToWiFi();
  client.setServer(mqtt_server, mqtt_port);
  connectToMQTT();
  startBLEBeacon();
}

void loop() {
  if (!client.connected()) connectToMQTT();
  client.loop();

  int n = WiFi.scanNetworks();
  for (int i = 0; i < n; ++i) {
    String ssidName = WiFi.SSID(i);
    if (ssidName == "RPi_AP_Pierre" || ssidName == "RPi_AP_Alicia" ||
        ssidName == "RPi_AP_KeeShen" || ssidName == "RPi_AP_EnThong") {
      String bssid = WiFi.BSSIDstr(i);
      int rssi = WiFi.RSSI(i);
      time_t now = time(nullptr);

      DynamicJsonDocument doc(256);
      doc["timestamp"] = getTimestamp();
      doc["timestamp_epoch"] = now;
      doc["ap_id"] = ssidName;
      doc["mac_address"] = bssid;
      doc["device_name"] = DEVICE_NAME;
      doc["rssi"] = rssi;

      char payload[256];
      serializeJson(doc, payload);
      client.publish(mqtt_topic_wifi, payload);
    }
  }
  delay(6000);
}
