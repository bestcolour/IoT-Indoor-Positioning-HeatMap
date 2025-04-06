# Steps to set up BLE-only architecture
## Configuring M5StickCPlus as a BLE beacon
- Change directory into "m5stickcplus_BLE", and ensure that the file "m5stickcplus_BLE.ino" is **uploaded** to your M5StickCPlus to configure your M5StickCPlus as a BLE beacon.
## Configuring Raspberry Pi as a MQTT Publisher
- Next, ensure that you have access to a Raspberry Pi and run the following commands to install bluepy.
(Skip to chained command below if you want to skip the step by step installation)
```
sudo apt-get update
```
```
mkdir IoTProject
```
```
cd IoTProject
```
```
sudo apt-get install git build-essential libglib2.0-dev 
```
```
git clone https://github.com/IanHarvey/bluepy.git
```
```
cd bluepy
```
```
python setup.py build
```
```
sudo python setup.py install
```

Chained commands (from `sudo apt-get update` to `sudo python setup.py install`):
```
sudo apt-get update && mkdir IoTProject && cd IoTProject && sudo apt-get install git build-essential libglib2.0-dev -y && git clone https://github.com/IanHarvey/bluepy.git && cd bluepy && python setup.py build && sudo python setup.py install
```

- Next, transfer the BLE_publisher.py code into the Raspberry Pi through SCP. 
```
scp BLE_publisher.py <hostname>@<RaspberryPiIPAddress>:/home/<hostname>/IoTProject/bluepy/
```

- Install the package paho-mqtt through the command (Skip to chained commands below if you want to skip the step by step installation)
```
sudo pip3 install --break-system-packages paho-mqtt
```
- Enable NTP on each Raspberry Pi
```
sudo timedatectl set-ntp true
```
```
sudo apt install ntpdate -y
```
```
sudo ntpdate time.google.com
```
```
sudo timedatectl set-timezone Asia/Singapore

```

The Chained Commands from `Install the package paho-mqtt` to `sudo timedatectl set-timezone Asia/Singapore`
```
sudo pip3 install --break-system-packages paho-mqtt && sudo timedatectl set-ntp true && sudo apt install ntpdate -y && sudo ntpdate time.google.com && sudo timedatectl set-timezone Asia/Singapore
```


- Run the following command to start the MQTT Publisher.
```
sudo python BLE_publisher.py
``` 


## Configuring another Raspberry Pi as the MQTT Broker
- Run the following commands.
```
sudo apt update
```
```
sudo apt install mosquitto mosquitto-clients -y
```
```
sudo systemctl enable mosquitto
```
```
sudo systemctl start mosquitto
```

- To setup authentication on the MQTT broker, run the following commands.
```
sudo nano /etc/mosquitto/mosquitto.conf
```
- Add these lines into the bottom of the file 
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```
Save the file by pressing **Ctrl + X**, then **Y**, then **Enter**
- Create a username and password for MQTT authentication (Replace team19 with your desired username)
```
sudo mosquitto_passwd -c /etc/mosquitto/passwd team19 
```
```
sudo systemctl restart mosquitto
```
## Starting the MQTT Subscriber
Run the following command:
```
python BLE_subscriber.py
```


## To load the latest estimated position data:
Run the below 2 commands to fetch the latest datas for filtered rssi and estimated positions:
```
python rssi_filter.py
```
```
python position_estimator.py
```