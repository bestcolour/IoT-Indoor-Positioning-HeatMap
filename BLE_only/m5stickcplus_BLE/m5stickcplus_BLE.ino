#include <M5StickCPlus.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

#define DEVICE_NAME "M5Stick_BLE"
#define SERVICE_UUID "12345678-1234-5678-1234-56789abcdef0"

void setup() {
    M5.begin();
    M5.Lcd.setRotation(1);  // Set display to landscape mode (USB on the right)
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setTextColor(GREEN);
    M5.Lcd.setTextSize(2);

    Serial.begin(115200);
    Serial.println("Starting BLE Beacon...");

    // Initialize BLE
    BLEDevice::init(DEVICE_NAME);
    BLEServer *pServer = BLEDevice::createServer();
    BLEService *pService = pServer->createService(SERVICE_UUID);
    pService->start();

    // Start BLE Advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(false);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();

    Serial.println("BLE Beacon Started!");

    // Get and display MAC Address
    std::string macAddress = BLEDevice::getAddress().toString();
    Serial.print("MAC Address: ");
    Serial.println(macAddress.c_str());

    // Display status on LCD
    M5.Lcd.setCursor(10, 10);
    M5.Lcd.println("BLE Beacon Active");

    M5.Lcd.setCursor(10, 40);
    M5.Lcd.println("Device name: " DEVICE_NAME);

    M5.Lcd.setCursor(10, 80);
    M5.Lcd.println("MAC: " + String(macAddress.c_str())); // Display MAC
}

void loop() {
    delay(1000); // Keep BLE running
}
