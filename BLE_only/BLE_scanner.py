import asyncio
from bleak import BleakScanner

async def scan_ble():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Device: {device.name} | Address: {device.address} | RSSI: {device.rssi} dBm")

asyncio.run(scan_ble())