# Hybrid mode setup
## Setting up Virtual Access Point (VAP) so that the Raspberry Pi can function as a BLE publisher and also an Access Point
### Step 1: Update and install dependencies
```
sudo apt update && sudo apt upgrade -y
```
```
sudo apt install -y network-manager dnsmasq hostapd iw net-tools dhcpcd5
```

Call this command in the case that there is an dhcpcd service running. If there is an error "Failed to disable unit: Unit file dhcpcd.service does not exist", ignore it and move on
```
sudo systemctl disable dhcpcd --now 
```

#### Chained Command (use this call `sudo apt update && sudo apt upgrade -y` to `sudo systemctl disable dhcpcd --now `):
```
sudo apt update && sudo apt upgrade -y && sudo apt install -y network-manager dnsmasq hostapd iw net-tools dhcpcd5 && sudo systemctl disable dhcpcd --now 
```

### Step 2: Configure NetworkManager to Handle wlan0 and Ignore uap0
```
sudo nano /etc/NetworkManager/NetworkManager.conf
```
Add under [main]:
```
dhcp=dhclient
```
Add at the end:
```
[keyfile]
unmanaged-devices=interface-name:uap0
```
```
sudo reboot
```

### Step 3: Create Virtual Access Point Interface (uap0)
Use scp to transfer the file "rclocal.sh" into your Raspberry Pi.
```
scp rclocal.sh <username>@<ipaddress>:/home/username/IoTProject/
```
On your Raspberry Pi, run:
```
sudo chmod +x rclocal.sh
```
```
sudo ./rclocal.sh
```

### Step 4: Configure Static IP for uap0
```
sudo nano /etc/dhcpcd.conf
```
#### Add this at the bottom. Replace 'x' with your desired IP address
```
interface uap0
    static ip_address=192.168.4.x/24
    nohook wpa_supplicant
```
```
sudo systemctl enable dhcpcd
sudo systemctl restart dhcpcd
```

### Step 5: Configure dnsmasq (DHCP for uap0)
```
sudo nano /etc/dnsmasq.d/uap0.conf
```
Add this:
```
interface=uap0
bind-interfaces
dhcp-range=192.168.4.100,192.168.4.200,255.255.255.0,24h
```
```
sudo systemctl enable dnsmasq
```

### Step 6: Configure hostapd (Wi-Fi AP on uap0)
```
sudo nano /etc/hostapd/hostapd_uap0.conf
```
```
interface=uap0
driver=nl80211
ssid=RPi_Hybrid_YourName
hw_mode=g
channel=6
auth_algs=1
wpa=2
wpa_passphrase=strongpassword123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```
```
sudo nano /etc/default/hostapd
```
Look for DAEMON_CONF, uncomment it and add the following:
```
DAEMON_CONF="/etc/hostapd/hostapd_uap0.conf"
```
```
sudo ln -s /etc/hostapd/hostapd_uap0.conf /etc/hostapd/hostapd.conf
```
```
sudo systemctl unmask hostapd && sudo systemctl enable hostapd && sudo systemctl restart hostapd && sudo systemctl restart dnsmasq
```

### Step 7: Save Wi-Fi Profile for BLE & Hybrid Modes
Replace "kys_dont_kys" and password below with your own network's ssid and password
```
sudo nmcli device wifi connect "kys_dont_kys" password "killmepls" name "kys_dont_kys"
```
You will need to reconnect through PuTTY after the previous command.
```
sudo nmcli connection modify kys_dont_kys connection.autoconnect yes
```


### Step 8: Create Mode Switching Scripts
Ensure that you are in the IoTProject directory.
```
sudo nano ./ble_only.sh
```
Add this in: RMB TO CHANGE "kys_dont_kys" TO YOUR SSID
```
#!/bin/bash
nmcli connection up kys_dont_kys  # Connect wlan0 to hotspot
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

```
sudo nano ./wifi_only.sh
```
Add this in, CHANGE THE IP TO THE ONE YOU HAVE SET ABOVE AT STEP4 and "kys_dont_kys" TO YOUR SSID:
```
#!/bin/bash
nmcli connection down kys_dont_kys
if ! ip addr show uap0 | grep -q "192.168.4.x"; then
  sudo ip addr add 192.168.4.x/24 dev uap0
fi
sudo systemctl restart dnsmasq
sudo systemctl restart hostapd
```

```
sudo nano ./hybrid_mode.sh
```
Add this in, CHANGE THE IP TO THE ONE YOU HAVE SET ABOVE AT STEP4 and "kys_dont_kys" TO YOUR SSID:
```
#!/bin/bash
nmcli connection up kys_dont_kys
if ! ip addr show uap0 | grep -q "192.168.4.x"; then
  sudo ip addr add 192.168.4.x/24 dev uap0
fi
sudo systemctl restart dnsmasq
sudo systemctl restart hostapd
```
Make them executable:
```
sudo chmod +x ble_only.sh wifi_only.sh hybrid_mode.sh
```

To run the scripts:
```
sudo ./ble_only.sh
```
```
sudo ./wifi_only.sh
```
```
sudo ./hybrid_mode.sh
```

## Transfer hybrid_publisher.py to all Raspberry Pis
```
scp hybrid_publisher.py <hostname>@<RaspberryPiIPAddress>:/home/<hostname>/IoTProject/bluepy/
```
## Run/compile the necessary files 
On the M5StickCPlus, upload the file **m5stickcplus_hybrid.ino**

Run the hybrid_publisher.py file on respective Raspberry Pis.
```
sudo python hybrid_publisher.py
```

Run the hybrid_subscriber.py file in the central processing unit (laptop).

## To load the latest estimated position data:
Run the below 2 commands to fetch the latest datas for filtered rssi and estimated positions:
```
python hybrid_rssi_filter.py
```
```
python hybrid_position_estimator.py
```