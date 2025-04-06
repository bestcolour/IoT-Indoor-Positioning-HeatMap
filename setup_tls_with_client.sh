#!/bin/bash

set -e

CERT_DIR=/etc/mosquitto/certs
SSL_CONF=/etc/mosquitto/conf.d/ssl.conf
PASSWORD_FILE=/etc/mosquitto/passwd

# Create certs directory
sudo mkdir -p $CERT_DIR
cd $CERT_DIR

echo "Generating Certificate Authority (CA)..."
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
  -subj "/C=SG/ST=SG/L=Singapore/O=IoTSystem/OU=CA/CN=IoTCA"

echo "Generating Server Certificate for CN=keshleepi.local..."
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/C=SG/ST=SG/L=Singapore/O=IoTSystem/OU=MQTT/CN=keshleepi.local"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -sha256

echo "Generating Client Certificate..."
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
  -subj "/C=SG/ST=SG/L=Singapore/O=IoTSystem/OU=Client/CN=M5StickClient"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days 365 -sha256

echo "Setting file permissions..."
sudo chown mosquitto:mosquitto $CERT_DIR/*.crt $CERT_DIR/*.key
sudo chmod 644 $CERT_DIR/*.crt
sudo chmod 600 $CERT_DIR/*.key

echo "Writing TLS configuration to $SSL_CONF..."
sudo tee $SSL_CONF > /dev/null <<EOF
listener 8883
protocol mqtt

cafile $CERT_DIR/ca.crt
certfile $CERT_DIR/server.crt
keyfile $CERT_DIR/server.key

require_certificate true
use_identity_as_username false

allow_anonymous false
password_file $PASSWORD_FILE
EOF

echo "Creating username/password file..."
sudo touch $PASSWORD_FILE
sudo mosquitto_passwd -b $PASSWORD_FILE team19 test123

echo "Restarting Mosquitto..."
sudo systemctl restart mosquitto

echo "TLS setup complete. Test with:"
echo "mosquitto_pub -h keshleepi.local -p 8883 \
  --cafile $CERT_DIR/ca.crt \
  --cert $CERT_DIR/client.crt \
  --key $CERT_DIR/client.key \
  -u team19 -P test123 \
  -t test/topic -m 'Hello from TLS client'"
