# Steps to set up WiFi-only architecture
## Configuring M5StickCPlus as a Wi-Fi RSSI scanner
- Change directory into "m5stickcplus_WiFi", and ensure that the file "m5stickcplus_WiFi.ino" is **uploaded** to your M5StickCPlus to configure your M5StickCPlus as a scanner.

## Configuring Raspberry Pi as an Access Point (AP)
### Step 1: Boot up and install required dependencies
```
sudo apt update && sudo apt upgrade -y
```

### Step 2: Enable ***dnsmasq** mode in NetworkManager
```
sudo nano /etc/NetworkManager/NetworkManager.conf
```

Add this line in the [main] section 
```
dns=dnsmasq
```

```
sudo systemctl restart NetworkManager
```

### Step 3: Create the DHCP range override 
```
sudo mkdir -p /etc/NetworkManager/dnsmasq.d
```
```
sudo nano /etc/NetworkManager/dnsmasq.d/ap-dhcp-range.conf
```
Paste this in:
```
dhcp-range=192.168.4.100,192.168.4.200,12h
```

### Step 4: Create the AP connection profile
```
sudo nmcli connection add type wifi ifname wlan0 con-name PiAP autoconnect yes ssid RPi_AP_yourname
```

### Step 5: Configure the AP with static IP and sharing
Replace x with your desired static IP
```
sudo nmcli connection modify PiAP 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv4.addresses 192.168.4.x/24
```

### Step 6: Set WPA2 security
```
sudo nmcli connection modify PiAP wifi-sec.key-mgmt wpa-psk wifi-sec.psk "strongpassword123"
```

### Step 7: Bring the AP online
```
sudo nmcli connection up PiAP
```

### Optional: Create ap_mode.sh and hotspot_mode.sh to switch between AP mode and hotspot mode easily
```
sudo nano ./ap_mode.sh
```
Paste this inside
```
#!/bin/bash

echo "Switching to AP Mode..."

# Optional: Disconnect from hotspot if connected
# sudo nmcli connection down "kys_dont_kys" 2>/dev/null

# Bring up the PiAP Access Point
sudo nmcli connection up PiAP

echo "Access Point 'RPi_AP_name' is now active with IP 192.168.4.x"
```
```
sudo chmod +x ap_mode.sh
```
### Hotspot_mode.sh
```
sudo nano ./hotspot_mode.sh
```
Paste this inside
```
#!/bin/bash

echo "Switching to Hotspot (Client) Mode..."

# Connect directly — NM will disable AP for you
sudo nmcli device wifi connect "kys_dont_kys" password "killmepls"
sudo nmcli connection modify "kys_dont_kys" connection.autoconnect yes
```
```
sudo chmod +x hotspot_mode.sh
```

## To load the latest estimated position data:
Run the below 2 commands to fetch the latest datas for filtered rssi and estimated positions:
```
python wifi_rssi_filter.py
```
```
python wifi_position_estimator.py
```