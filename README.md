# IoT-Indoor-Positioning-HeatMap
This project was developed as part of the Year 2 CSC2106 Internet of Things module. It explores an indoor positioning system that utilizes trilateration and filtering/smoothing algorithms applied to BLE and Wi-Fi signals. The goal is to evaluate the effectiveness of BLE-only, Wi-Fi-only, and Hybrid (BLE + Wi-Fi) approaches in tracking shoppers within a simulated supermarket environment.

## Project Structure
- `BLE_only/` – Code for BLE-based setup (scanning, publishing, and subscribing)
- `Wifi_only/` – Code for Wi-Fi-based setup (RSSI scanning and publishing)
- `BLE+Wifi/` – Code for the hybrid setup (combined BLE and Wi-Fi positioning)
- `flask-project/` – Web dashboard built with Flask to visualize collected data and heatmaps
- `setup_tls_with_client.sh` – Script to configure TLS for Mosquitto MQTT broker and generate client/server certificates
- `positioning.db` – SQLite database for storing real-time RSSI data and processed results

## Install the required dependencies
```
pip install -r requirements.txt
```

## TLS Setup for MQTT Secure Communication (Mosquitto Broker + Clients)
This guide walks you through setting up TLS 1.3 for Mosquitto MQTT communication using X.509 certificates and a trusted local Certificate Authority (CA). This setup ensures encrypted communication, integrity, and authentication between the broker and clients.

#### 1. Edit the script **setup_tls_with_client.sh**, replacing "keshleepi.local" with the hostname of your Raspberry Pi.
Then transfer the script to your Raspberry Pi using scp.
### 2. Run the following commands on your Raspberry Pi MQTT broker
```
chmod +x setup_tls_with_client.sh
sudo ./setup_tls_with_client.sh
```
#### 3. After running the script, the /etc/mosquitto/certs/ directory should contain:
- ca.crt 
- ca.key 
- server.crt 
- server.key 
- client.crt 
- client.key 

#### 4. Set Up Clients (BLE Publisher / Wi-Fi Publisher / Subscribers)
On each device (e.g., Raspberry Pi BLE scanner, Wi-Fi scanner, Windows/Linux subscriber), copy the certs:
```
scp <username>@<hostname>:/etc/mosquitto/certs/ca.crt .
scp <username>@<hostname>:/etc/mosquitto/certs/client.crt .
scp <username>@<hostname>:/etc/mosquitto/certs/client.key .
```
Place them in a folder like `certs/` in your project directory (The `certs/` folder should be at the same folder as your publisher/subscriber script).

#### 5. Update Client Code to Use TLS
```
client.tls_set(
    ca_certs="certs/ca.crt",
    certfile="certs/client.crt",
    keyfile="certs/client.key"
)
client.username_pw_set("mqttusername", "mqttpassword")
client.connect("hostname", 8883)
```
Optionally, add client.tls_insecure_set(True) if using IP instead of hostname and the CN doesn't match.

#### 6. M5StickCPlus
The TLS certificate information is hardcoded in the .ino files. Simply replace them with your own or fill up this template to be used when connecting to a mosquitto broker.

**Template**
``` C

const char* ca_cert = R"(
-----BEGIN CERTIFICATE-----
<certificate key>
-----END CERTIFICATE-----
)";

const char* client_cert = R"(
-----BEGIN CERTIFICATE-----
<certificate key>
-----END CERTIFICATE-----
)";

const char* client_key = R"(
-----BEGIN PRIVATE KEY-----
<certificate key>
-----END PRIVATE KEY-----
)";

```