#include <M5StickCPlus.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>  // Include WiFiClientSecure for secure MQTT
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
const char* mqtt_server = "keshleepi.local";
const int mqtt_port = 8883;  // Use port 8883 for secure MQTT
const char* mqtt_user = "team19";
const char* mqtt_password = "test123";
const char* mqtt_topic_wifi = "wifi/rssi";

// === Device Identity ===
const char* DEVICE_NAME = "M5StickCPlus-XinYi";

// === BLE Beacon UUID (per team/personal) ===
#define BEACON_UUID "12345678-9012-3456-7890-1234567890AB"

// === Certificates (replace with your actual certificate content) ===

const char* ca_cert = R"(
-----BEGIN CERTIFICATE-----
MIIDnzCCAoegAwIBAgIUdnWorjDwjlfbBRXGZrLjPheahFowDQYJKoZIhvcNAQEL
BQAwXzELMAkGA1UEBhMCU0cxCzAJBgNVBAgMAlNHMRIwEAYDVQQHDAlTaW5nYXBv
cmUxEjAQBgNVBAoMCUlvVFN5c3RlbTELMAkGA1UECwwCQ0ExDjAMBgNVBAMMBUlv
VENBMB4XDTI1MDQwNjAwMzcyM1oXDTM1MDQwNDAwMzcyM1owXzELMAkGA1UEBhMC
U0cxCzAJBgNVBAgMAlNHMRIwEAYDVQQHDAlTaW5nYXBvcmUxEjAQBgNVBAoMCUlv
VFN5c3RlbTELMAkGA1UECwwCQ0ExDjAMBgNVBAMMBUlvVENBMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEA5n8RRcrIZkb8C3YjS+fq4OtMGInCDWU8Pz2o
+cl68ekIeMTK8AvTxBz2W9bwTQrWF6+n7GoliV5A9NDQLWDsdxjgI48ZNIPUfIv2
qjlzgh4V664pMJ/J9cFJIuxU1J4lRbaqKWBzssCJmLGnBB+g3NzELC+jBWrb1LdM
Njo8P1k+34c7nC6yE1kvnH7cXgSkkSgGjfCM06TJ7BVwjKJHuwtporUu6PfIBF4K
t5RXwmggPdEcK0j0iv8zuOabpIMgUU3FOqhZwrSpU/OsgjW9U4cKeyDBAWtj+upU
FViHI2eLCVLCE8f6ZxANDA6+F3wTRjgLeSDR/DZy4BTtQfiRMwIDAQABo1MwUTAd
BgNVHQ4EFgQUjovo8HLJGvsseIa3NfAD3M9Bfo4wHwYDVR0jBBgwFoAUjovo8HLJ
GvsseIa3NfAD3M9Bfo4wDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOC
AQEAlFhM3z9LmiUbWjxZulpYAXODwXmcvQsWdKnVCC9xO7l8QAj+y428o/zs6W3B
41UYEzbULRnURaFKIDMU9hh6g2bbrhENHYkdfSvhMa508VDAysKZgYfhtdQqnEy3
YUK1Xaj36tXyZTr4vkrB2niBvBnZYMSQ4lxwoF4mhB4RlaZJd3i6yryFdafDZEeN
Dzwogx4FtVIa5U/SCCGNBeLV0WaAH71MPSbzTl8yEZEnFEZXqzu0Gu45SUGu3+tQ
n1BwCoXdvX3wciNgbsqAIOLuxExK2Sv4vLuNlezIUeqFADJHj0jEqQyci2+8B5zy
0qygUTVVlrwYW5Oo5m2M6U0fnw==
-----END CERTIFICATE-----
)";

const char* client_cert = R"(
-----BEGIN CERTIFICATE-----
MIIDUTCCAjkCFF4Ju3PqCUky3FmG6ata6UhL79GgMA0GCSqGSIb3DQEBCwUAMF8x
CzAJBgNVBAYTAlNHMQswCQYDVQQIDAJTRzESMBAGA1UEBwwJU2luZ2Fwb3JlMRIw
EAYDVQQKDAlJb1RTeXN0ZW0xCzAJBgNVBAsMAkNBMQ4wDAYDVQQDDAVJb1RDQTAe
Fw0yNTA0MDYwMDM3MjVaFw0yNjA0MDYwMDM3MjVaMGsxCzAJBgNVBAYTAlNHMQsw
CQYDVQQIDAJTRzESMBAGA1UEBwwJU2luZ2Fwb3JlMRIwEAYDVQQKDAlJb1RTeXN0
ZW0xDzANBgNVBAsMBkNsaWVudDEWMBQGA1UEAwwNTTVTdGlja0NsaWVudDCCASIw
DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJ9sO5vaAAuxvbS0vCqfS930AiIh
a+JdrAT+dkm6QOJo3q5sXX4uko/IO7TEjd5GPsVdVfdHrl9oFaK20uxJNeFeY3Jz
9+a2DMuNEvwqgkzqMe/Ig4Y4lT9kOpvR3bk0sgQ4dbSX1XpE8h5h0lid5H9rqTtu
5yVercGW2jLbXBJTaPYGfWTF1d/lkqGWBwy6osHduFTmEorfLEr2tlKLQRXQ5nZ/
2clnRUWrUGhgSkCngdWSHBJfFNnoK5Dcp2kru7oOaN2PTARqKXsQAb9IsES1Oon1
R7ayPDRg6nAlShHs21Z1vDkxjn7ZS0GeQbsJpskc1QFmOkqw+hVVzY/dJ1kCAwEA
ATANBgkqhkiG9w0BAQsFAAOCAQEABvwPXOsAKpyk3ZwBF6mNgeskrPyP0dI8+s6J
L1aY3lH7QMIuEN1xazlNtengPFTOjfiYHbvbOHBvtJdJzapxCmObBbwame7Sh56h
4kipx5vDYhy/8guUjwHvhxEzlc63aFrWdrCFdW+sTvMOAPeRjmsQMK3HwsrgqdHE
bFYhwG8I0Kq0LWbJk8oDlg4EVeItW0ydr7dKHpTLe1TSk7+Gx3tJv7CsS0abMaBU
NozbypDfKzeU3eFUfKoLpNxt5zNm5HDXWp3+v3dCAVCS033Lu/3hf5RqBh43Nisy
iUvi5TlJ+WWaEFl4qrPVlO7okBAQ9+Zzd5cCaJF/PC82AHLfAA==
-----END CERTIFICATE-----
)";

const char* client_key = R"(
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCfbDub2gALsb20
tLwqn0vd9AIiIWviXawE/nZJukDiaN6ubF1+LpKPyDu0xI3eRj7FXVX3R65faBWi
ttLsSTXhXmNyc/fmtgzLjRL8KoJM6jHvyIOGOJU/ZDqb0d25NLIEOHW0l9V6RPIe
YdJYneR/a6k7buclXq3Bltoy21wSU2j2Bn1kxdXf5ZKhlgcMuqLB3bhU5hKK3yxK
9rZSi0EV0OZ2f9nJZ0VFq1BoYEpAp4HVkhwSXxTZ6CuQ3KdpK7u6Dmjdj0wEail7
EAG/SLBEtTqJ9Ue2sjw0YOpwJUoR7NtWdbw5MY5+2UtBnkG7CabJHNUBZjpKsPoV
Vc2P3SdZAgMBAAECggEALo3qsk5s6P1UiqqksEWoX/5biR/9YzM7gpHUdR9Ax10c
eg8HFkv/XKF6XgVv8FLPDc99xSJXl2DLwKJm4b1XUKLBo7Cd2e+buO1Pd/fp6RAS
2RTS46UuYD6iptIYT3dF7NmX9c7I9lWf5qNmS56AFX2ZA9QVB+KoFvo4adWJA4iF
cWaVuPfzeQiPWGClqimrDu0N4xhScrEJhJ+OAsZunz5RgOIOoLQ99S7mNb8ajs0N
ahDpBU2Saz7LGua+OujD8rP8shcz/Ohm10F2lEIwnZodfunvBqN0LnH9P8tmeZvt
gLfLim2yMnsauZYfYs1AEJzOAnegr2XImnFFD+/kaQKBgQDfJbKDuUMKYCbJt7eo
yOHyBbzHlZJWtWFBFzeIuCcSLu/az8Ae3ivCw1InJ5isWJnxk2sGZbrTm8/udfDI
ydu2DXDXIwuQquwcASYStplrXZub7o8RkyP39cmPWkGjTLDW2GxuvsxW1Nm7x3XE
sdvXziPFbqvrSt0wDbKWa2zqJwKBgQC25Msy2ONyo5ExSpuXjypMMF6D3EVmc45J
8HLRAaAePTLYq7RCd2gm3GM6eS8zWa2tfAq9F5eoawzkBYVdD9lw7zRpOTEQV7HZ
lHLihGhBPYeIfsf3y+7cY/aFQE+Yr1F8QdMY9Xg7AX14kTwV3RuvYwfY0cNIPmxV
yOdBStfSfwKBgGH4JgDpBIL4pe7oBu1GjNR6KmChzWbeKT2vmMUgvJ6iFtJFZb7n
oeTXZikknEYGfEfwhgt//F9NSCQUictNvHWYPxNlIn24XQMKihGrM35M0bXLLer0
Y9VIht62LJ0qXXVl/W09vW7d8l4b+xuJTtDXgyL6LOaXrrabPO4HagD/AoGAWD6a
QGVfkN+U3YiW/BCKowovgEXWgnE89TX74BZ9sDltABgQuIUujpmFkyAHgypA31Tb
RZNNjGhiZt63E0jjbFcuHZsHrk/xsv6qU9r5BolujJBHYatXC6V7u51lClGE6oRE
G2XM5gN5C6Rfrljp07zfe2DybTgZQ2bVFa7L5XcCgYEA2YZAU0q2Jp+ul0SZUlKm
1Srq53PxYTBVrbUjZhTa0DS1/eoWK6/ljJgvlqgCmp3rTnDZFkwZ1UHQeB8tW72K
bFRRS05FAXAY8wwGPsZm1y7GTyBqkdt04AaYpNfKOzc7Dh2Wls1CdyzJ0cygirkW
3p5mHAZ+/kBfyXeGKmQZaAI=
-----END PRIVATE KEY-----
)";

WiFiClientSecure espClient;  // Use WiFiClientSecure for secure connection
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

  configTime(28800, 0, "time.google.com");  // UTC+8 for Singapore
  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    now = time(nullptr);
  }
  M5.Lcd.println("Time synced");
}

void connectToMQTT() {
  M5.Lcd.println("Connecting to MQTT...");
  // Set the certificates for secure connection
  espClient.setCACert(ca_cert);        // Set CA certificate
  espClient.setCertificate(client_cert);  // Set client certificate
  espClient.setPrivateKey(client_key);   // Set client private key

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
