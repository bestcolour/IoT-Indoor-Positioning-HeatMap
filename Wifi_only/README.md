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

Add this line
```
dns=dnsmasq
```
in the [main] section 

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