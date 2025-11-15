# Home Assistant Quick Start Guide

## 🏠 One-Command Setup for Home Assistant

### Step 1: Install Dependencies
```bash
pip3 install --break-system-packages -r requirements.txt
```

### Step 2: Run the MQTT Bridge
```bash
# If MQTT broker is on same machine as Home Assistant
python3 homeassistant_mqtt.py

# If MQTT broker is on different machine
python3 homeassistant_mqtt.py --mqtt-host YOUR_HA_IP_ADDRESS
```

### Step 3: Check Home Assistant
- Go to **Settings** → **Devices & Services** → **MQTT**
- Your Teltonika EYE sensors will appear automatically!

## 🎯 What You Get

### Automatic Sensors
- 🌡️ **Temperature** (°C)
- 💧 **Humidity** (%)
- 🔋 **Battery Voltage** (V)
- 🚶 **Movement Detection** (ON/OFF)
- 📊 **Movement Count** (total events)
- 🧲 **Magnetic Field** (detected/not detected)
- 📐 **Orientation** (pitch/roll angles)
- 📶 **Signal Strength** (RSSI)
- ⚠️ **Low Battery Alert**

### Example Entity Names
```
sensor.logikai_2es_temperature
sensor.logikai_2es_humidity
sensor.logikai_2es_battery
binary_sensor.logikai_2es_movement_state
binary_sensor.logikai_2es_low_battery
```

## 🔧 Configuration Options

### Basic Usage
```bash
python3 homeassistant_mqtt.py
```

### Custom MQTT Settings
```bash
python3 homeassistant_mqtt.py \
    --mqtt-host 192.168.1.100 \
    --mqtt-username homeassistant \
    --mqtt-password your_password
```

### Custom Scan Settings
```bash
python3 homeassistant_mqtt.py \
    --scan-duration 5 \
    --scan-interval 30
```

## 📱 Example Dashboard Card

Add this to your Home Assistant dashboard:

```yaml
type: entities
title: Teltonika EYE Sensors
entities:
  - sensor.logikai_2es_temperature
  - sensor.logikai_2es_humidity
  - sensor.logikai_2es_battery
  - binary_sensor.logikai_2es_movement_state
  - binary_sensor.logikai_2es_low_battery
```

## 🚨 Example Automation

```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.logikai_2es_temperature
        above: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Temperature is {{ trigger.to_state.state }}°C!"
```

## 🔄 Run as Service

Create `/etc/systemd/system/teltonika-ha.service`:
```ini
[Unit]
Description=Teltonika EYE Home Assistant Bridge
After=network.target

[Service]
Type=simple
User=homeassistant
WorkingDirectory=/path/to/teltonika-ble
ExecStart=/usr/bin/python3 homeassistant_mqtt.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable teltonika-ha.service
sudo systemctl start teltonika-ha.service
```

## ✅ Features

- **Zero Configuration**: Sensors appear automatically
- **No Logging**: Home Assistant handles all logging
- **Multiple Sensors**: Supports unlimited sensors
- **Real-time Updates**: Configurable scan intervals
- **Battery Monitoring**: Low battery alerts
- **Device Classes**: Proper Home Assistant integration
- **Auto-Discovery**: No manual YAML configuration needed

## 🆘 Troubleshooting

### No Sensors Appearing?
1. Check MQTT is configured in Home Assistant
2. Verify sensors are powered and in range
3. Check Bluetooth permissions: `sudo usermod -a -G bluetooth $USER`

### MQTT Connection Issues?
```bash
# Test MQTT connection
mosquitto_pub -h localhost -t test -m "hello"
```

That's it! Your Teltonika EYE sensors will now appear in Home Assistant automatically! 🎉