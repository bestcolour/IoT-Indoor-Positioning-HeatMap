#include <M5StickCPlus.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>
#include <BLEServer.h>

// === Wi-Fi credentials ===
const char* ssid = "kys_dont_kys";
const char* password = "killmepls";

// === MQTT broker config ===
const char* mqtt_server = "192.168.33.148";
const int mqtt_port = 1883;
const char* mqtt_user = "team19";
const char* mqtt_password = "test123";
const char* mqtt_topic_wifi = "wifi/rssi";

// === Device Identity ===
const char* DEVICE_NAME = "M5StickCPlus-XinYi";

// === BLE Beacon UUID (per team/personal) ===
#define BEACON_UUID "12345678-9012-3456-7890-1234567890AB"

WiFiClient espClient;
PubSubClient client(espClient);

// === BLE beacon setup ===
void startBLEBeacon() {
  BLEDevice::init(DEVICE_NAME);
  BLEServer* pServer = BLEDevice::createServer();

  // Custom service (used for basic advertisement)
  BLEService* pService = pServer->createService("12345678-1234-5678-1234-56789abcdef0");
  pService->start();

  // Start advertising
  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID("12345678-1234-5678-1234-56789abcdef0");
  pAdvertising->setScanResponse(true); // Needed to advertise the name
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("BLE Beacon Started!");
  Serial.println("Device Name: " + String(DEVICE_NAME));

  std::string macAddress = BLEDevice::getAddress().toString();
  Serial.print("MAC Address: ");
  Serial.println(macAddress.c_str());

  // Display on M5
  M5.Lcd.setCursor(10, 10);
  M5.Lcd.println("BLE Beacon Active");
  M5.Lcd.setCursor(10, 40);
  M5.Lcd.println("MAC: " + String(macAddress.c_str()));
}

void connectToWiFi() {
  M5.Lcd.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
  }
  M5.Lcd.println("\nWiFi Connected!");
  M5.Lcd.println(WiFi.localIP());

  configTime(0, 0, "time.google.com");
  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    now = time(nullptr);
  }
  M5.Lcd.println("Time synced");
}

void connectToMQTT() {
  M5.Lcd.println("Connecting to MQTT...");
  while (!client.connected()) {
    if (client.connect(DEVICE_NAME, mqtt_user, mqtt_password)) {
      M5.Lcd.println("MQTT Connected");
    } else {
      M5.Lcd.printf("MQTT failed (%d)\n", client.state());
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
  M5.Lcd.setRotation(3);  // Landscape
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Initializing...");
  M5.Lcd.println(DEVICE_NAME);

  connectToWiFi();
  client.setServer(mqtt_server, mqtt_port);
  connectToMQTT();
  startBLEBeacon();

  // Clear and show final screen after setup
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.println(DEVICE_NAME);
  M5.Lcd.println("In BLE Beacon mode..");
  M5.Lcd.println("Scanning for Wi-Fi RSSI..");
}

void loop() {
  if (!client.connected()) connectToMQTT();
  client.loop();

  int n = WiFi.scanNetworks();
  M5.Lcd.fillRect(0, 40, 135, 90, BLACK);  // Clear only the lower part for RSSI values
  M5.Lcd.setCursor(0, 40);

  for (int i = 0; i < n; ++i) {
    String ssidName = WiFi.SSID(i);

    if (ssidName == "RPi_Hybrid_Pierre" || ssidName == "RPi_Hybrid_Alicia" ||
        ssidName == "RPi_Hybrid_XinYi" || ssidName == "RPi_Hybrid_EnThong") {

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

      // Display SSID name
      M5.Lcd.setTextSize(1);
      M5.Lcd.setTextColor(WHITE);
      M5.Lcd.printf("%s\n", ssidName.c_str());

      // Display RSSI
      M5.Lcd.setTextSize(1);
      M5.Lcd.setTextColor(GREEN);
      M5.Lcd.printf("RSSI: %d dBm\n", rssi);
    }
  }

  delay(6000);
}
