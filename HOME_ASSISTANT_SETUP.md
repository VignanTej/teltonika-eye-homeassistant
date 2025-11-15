# Home Assistant Integration for Teltonika EYE Sensors

This guide shows how to integrate Teltonika EYE sensors with Home Assistant using MQTT auto-discovery.

## Quick Setup

### 1. Install Dependencies
```bash
pip3 install --break-system-packages -r requirements.txt
```

### 2. Configure MQTT in Home Assistant

Add to your `configuration.yaml`:
```yaml
mqtt:
  broker: localhost  # Your MQTT broker IP
  port: 1883
  discovery: true
  discovery_prefix: homeassistant
```

### 3. Run the MQTT Bridge
```bash
# Basic setup (MQTT broker on localhost)
python3 homeassistant_mqtt.py

# Custom MQTT broker
python3 homeassistant_mqtt.py --mqtt-host 192.168.1.100

# With authentication
python3 homeassistant_mqtt.py \
    --mqtt-host 192.168.1.100 \
    --mqtt-username your_username \
    --mqtt-password your_password
```

### 4. Sensors Auto-Appear in Home Assistant

Once running, sensors will automatically appear in Home Assistant with names like:
- `sensor.teltonika_eye_temperature`
- `sensor.teltonika_eye_humidity`
- `sensor.teltonika_eye_battery`
- `binary_sensor.teltonika_eye_movement_state`
- `binary_sensor.teltonika_eye_magnetic`

## What Gets Created in Home Assistant

### Sensors Created Per Device

| Sensor Type | Entity ID | Description |
|-------------|-----------|-------------|
| Temperature | `sensor.{device}_temperature` | Temperature in °C |
| Humidity | `sensor.{device}_humidity` | Relative humidity % |
| Battery Voltage | `sensor.{device}_battery` | Battery voltage in V |
| Movement Count | `sensor.{device}_movement_count` | Total movement events |
| Movement State | `binary_sensor.{device}_movement_state` | Currently moving (ON/OFF) |
| Magnetic Field | `binary_sensor.{device}_magnetic` | Magnetic field detected |
| Pitch Angle | `sensor.{device}_pitch` | Device pitch angle |
| Roll Angle | `sensor.{device}_roll` | Device roll angle |
| Signal Strength | `sensor.{device}_rssi` | Bluetooth signal strength |
| Low Battery | `binary_sensor.{device}_low_battery` | Low battery warning |

### Device Information

Each sensor appears as a complete device in Home Assistant with:
- **Manufacturer**: Teltonika
- **Model**: EYE Sensor
- **Identifiers**: Unique device ID based on MAC address
- **Software Version**: Protocol version

## MQTT Topics Structure

### Discovery Topics (Auto-created)
```
homeassistant/sensor/teltonika_eye_{device_id}/temperature/config
homeassistant/sensor/teltonika_eye_{device_id}/humidity/config
homeassistant/binary_sensor/teltonika_eye_{device_id}/movement_state/config
# ... etc for each sensor type
```

### State Topics (Data)
```
teltonika_eye/{device_id}/temperature
teltonika_eye/{device_id}/humidity
teltonika_eye/{device_id}/movement_count
teltonika_eye/{device_id}/movement_state
teltonika_eye/{device_id}/magnetic
teltonika_eye/{device_id}/battery
teltonika_eye/{device_id}/pitch
teltonika_eye/{device_id}/roll
teltonika_eye/{device_id}/rssi
teltonika_eye/{device_id}/low_battery
teltonika_eye/{device_id}/state  # Complete JSON state
```

## Example Automations

### Temperature Alert
```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.teltonika_eye_*_temperature
        above: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "High Temperature"
          message: "{{ trigger.entity_id }} reports {{ trigger.to_state.state }}°C"
```

### Movement Detection
```yaml
automation:
  - alias: "Movement Detected"
    trigger:
      - platform: state
        entity_id: binary_sensor.teltonika_eye_*_movement_state
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.hallway
```

### Low Battery Notification
```yaml
automation:
  - alias: "Sensor Low Battery"
    trigger:
      - platform: state
        entity_id: binary_sensor.teltonika_eye_*_low_battery
        to: 'on'
    action:
      - service: notify.persistent_notification
        data:
          title: "Sensor Battery Low"
          message: "{{ trigger.entity_id }} needs battery replacement"
```

## Dashboard Cards

### Simple Sensor Card
```yaml
type: entities
title: Teltonika EYE Sensors
entities:
  - sensor.teltonika_eye_temperature
  - sensor.teltonika_eye_humidity
  - sensor.teltonika_eye_battery
  - binary_sensor.teltonika_eye_movement_state
```

### Gauge Card for Temperature
```yaml
type: gauge
entity: sensor.teltonika_eye_temperature
min: 0
max: 50
severity:
  green: 0
  yellow: 25
  red: 35
```

### History Graph
```yaml
type: history-graph
entities:
  - sensor.teltonika_eye_temperature
  - sensor.teltonika_eye_humidity
hours_to_show: 24
```

## Production Deployment

### Systemd Service

Create `/etc/systemd/system/teltonika-mqtt.service`:
```ini
[Unit]
Description=Teltonika EYE MQTT Bridge
After=network.target bluetooth.service

[Service]
Type=simple
User=homeassistant
WorkingDirectory=/opt/teltonika-ble
ExecStart=/usr/bin/python3 homeassistant_mqtt.py --mqtt-host localhost
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/teltonika-ble

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable teltonika-mqtt.service
sudo systemctl start teltonika-mqtt.service
```

### Docker Compose

```yaml
version: '3.8'
services:
  teltonika-mqtt:
    build: .
    restart: unless-stopped
    privileged: true  # Required for Bluetooth access
    network_mode: host
    environment:
      - MQTT_HOST=localhost
      - SCAN_INTERVAL=30
    volumes:
      - /var/run/dbus:/var/run/dbus:ro
```

### Home Assistant Add-on

For Home Assistant OS, you can create a custom add-on:

`config.yaml`:
```yaml
name: Teltonika EYE MQTT Bridge
version: 1.0.0
slug: teltonika_eye_mqtt
description: Bridge for Teltonika EYE sensors
arch:
  - aarch64
  - amd64
  - armhf
  - armv7
  - i386
init: false
options:
  mqtt_host: core-mosquitto
  scan_interval: 30
schema:
  mqtt_host: str
  mqtt_port: int(1883)
  mqtt_username: str?
  mqtt_password: password?
  scan_interval: int(30)
  scan_duration: int(5)
```

## Troubleshooting

### No Sensors Appearing
1. Check MQTT broker connection
2. Verify Home Assistant MQTT discovery is enabled
3. Check Bluetooth permissions
4. Ensure sensors are in range and powered

### MQTT Connection Issues
```bash
# Test MQTT connection
mosquitto_pub -h localhost -t test/topic -m "test message"

# Monitor MQTT traffic
mosquitto_sub -h localhost -t "homeassistant/+/teltonika_eye_+/+/config"
mosquitto_sub -h localhost -t "teltonika_eye/+/+"
```

### Bluetooth Issues
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Reset Bluetooth adapter
sudo hciconfig hci0 down && sudo hciconfig hci0 up

# Check permissions
groups $USER | grep bluetooth
```

## Advanced Configuration

### Custom Device Names
Sensors will use their advertised name or default to "Teltonika EYE {MAC}". You can customize names in Home Assistant after discovery.

### Multiple MQTT Brokers
Run separate instances for different MQTT brokers:
```bash
python3 homeassistant_mqtt.py --mqtt-host broker1.local &
python3 homeassistant_mqtt.py --mqtt-host broker2.local --discovery-prefix homeassistant2 &
```

### Custom Scan Intervals
```bash
# High frequency (every 10 seconds)
python3 homeassistant_mqtt.py --scan-interval 10

# Low frequency (every 5 minutes)
python3 homeassistant_mqtt.py --scan-interval 300
```

## Features

✅ **Auto-Discovery**: Sensors automatically appear in Home Assistant  
✅ **No Logging**: Home Assistant handles all logging  
✅ **Multiple Sensors**: Supports unlimited sensors simultaneously  
✅ **Real-time Updates**: Configurable scan intervals  
✅ **Device Classes**: Proper Home Assistant device classes for all sensors  
✅ **Battery Monitoring**: Low battery alerts and voltage monitoring  
✅ **Signal Strength**: RSSI monitoring for connectivity issues  
✅ **Complete State**: Full JSON state available for advanced automations  

The integration is designed to be maintenance-free once configured!