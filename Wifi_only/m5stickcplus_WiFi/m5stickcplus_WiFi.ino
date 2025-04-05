#include <M5StickCPlus.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

// === Wi-Fi credentials ===
const char* ssid     = "kys_dont_kys";
const char* password = "killmepls";

// === MQTT broker settings ===
const char* mqtt_server   = "192.168.33.148";
const int   mqtt_port     = 1883;
const char* mqtt_user     = "team19";
const char* mqtt_password = "test123";
const char* mqtt_topic    = "wifi/rssi";

// === AP Scanner identity ===
const char* DEVICE_NAME = "M5StickCPlus-KeeShen";

WiFiClient espClient;
PubSubClient client(espClient);

const unsigned long publishInterval = 6000;  // 6 seconds

// === Connect to Wi-Fi ===
void connectToWiFi() {
  M5.Lcd.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
  }
  M5.Lcd.println("\nWiFi Connected!");
  M5.Lcd.println(WiFi.localIP());

  configTime(0, 0, "time.google.com");  // Set up NTP
  M5.Lcd.println("Syncing time...");
  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    now = time(nullptr);
  }
  M5.Lcd.println("Time synced.");
}

// === Connect to MQTT ===
void connectToMQTT() {
  M5.Lcd.println("Connecting to MQTT...");
  while (!client.connected()) {
    if (client.connect("M5StickClient", mqtt_user, mqtt_password)) {
      M5.Lcd.println("MQTT Connected");
    } else {
      M5.Lcd.printf("MQTT failed, rc=%d. Retrying...\n", client.state());
      delay(2000);
    }
  }
}

// === Get current timestamp ===
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
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Wi-Fi RSSI MQTT Scanner");

  WiFi.mode(WIFI_STA);
  connectToWiFi();

  client.setServer(mqtt_server, mqtt_port);
  connectToMQTT();
}

void loop() {
  unsigned long startCycle = millis();

  // Show "Scanning" status
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.setTextSize(3);
  M5.Lcd.setCursor(20, 20);
  M5.Lcd.println("Scanning");

  M5.Lcd.setTextSize(1);
  M5.Lcd.setCursor(20, 60);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.println(DEVICE_NAME);

  // Start synchronous scan
  int n = WiFi.scanNetworks();  // blocking

  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.printf("Found %d networks\n", n);

  for (int i = 0; i < n; ++i) {
    String ssidName = WiFi.SSID(i);

    if (ssidName == "RPi_AP_Pierre" || ssidName == "RPi_AP_Alicia" ||
        ssidName == "RPi_AP_KeeShen" || ssidName == "RPi_AP_EnThong") {

      String bssid = WiFi.BSSIDstr(i);
      int rssi = WiFi.RSSI(i);

      DynamicJsonDocument doc(256);
      doc["timestamp"] = getTimestamp();
      doc["timestamp_epoch"] = time(nullptr); // epoch timestamp to calculate latency
      doc["ap_id"] = ssidName;
      doc["mac_address"] = bssid;
      doc["device_name"] = DEVICE_NAME;
      doc["rssi"] = rssi;

      char payload[256];
      serializeJson(doc, payload);

      if (!client.connected()) {
        connectToMQTT();
      }
      client.loop();
      if (client.publish(mqtt_topic, payload)) {
        Serial.println("Published:");
        Serial.println(payload);
      } else {
        Serial.println("MQTT publish failed!");
      }

      M5.Lcd.printf("%s (%d dBm)\n", ssidName.c_str(), rssi);
      delay(100);  // pacing between publishes
    }
  }

  // Wait out remaining time to hit 6 seconds
  unsigned long elapsed = millis() - startCycle;
  if (elapsed < publishInterval) {
    delay(publishInterval - elapsed);
  }
}
