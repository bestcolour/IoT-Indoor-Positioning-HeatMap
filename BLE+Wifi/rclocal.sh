# 1. Create /etc/rc.local with your VAP line
sudo tee /etc/rc.local > /dev/null <<'EOF'
#!/bin/bash
# Create VAP interface on boot
/sbin/iw dev wlan0 interface add uap0 type __ap
exit 0
EOF

# 2. Make it executable
sudo chmod +x /etc/rc.local

# 3. Create systemd service file
sudo tee /etc/systemd/system/rc-local.service > /dev/null <<'EOF'
[Unit]
Description=/etc/rc.local Compatibility
ConditionPathExists=/etc/rc.local
After=network.target

[Service]
Type=forking
ExecStart=/etc/rc.local
TimeoutSec=0
RemainAfterExit=yes
GuessMainPID=no

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start the service
sudo systemctl enable rc-local
sudo systemctl start rc-local
