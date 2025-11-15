# Teltonika EYE Sensors - Home Assistant Custom Integration v1.1.0

A native Home Assistant custom integration for Teltonika EYE sensors with **Bluetooth proxy support** and **enhanced device discovery**.

## 🎉 New in v1.1.0

### ✅ Bluetooth Proxy Support
- **Full ESP32 Bluetooth proxy compatibility**
- **Extended range** through distributed proxy network
- **Better reliability** via Home Assistant's Bluetooth integration
- **Real-time updates** through advertisement callbacks

### ✅ Enhanced Device Discovery
- **User-controlled onboarding** - Choose which devices to monitor
- **Discovery notifications** - Get notified when new sensors are found
- **Device management** - Approve or ignore devices through UI
- **Live sensor data** - See current readings during device selection

### ✅ Bug Fixes
- **Fixed magnetic sensor logic** - Now correctly reports open/closed states
- **Improved performance** - Event-driven architecture instead of polling

## Features

- **Bluetooth Proxy Compatible**: Works with ESP32 Bluetooth proxies for extended range
- **Smart Discovery**: User-controlled device onboarding with notifications
- **Multiple Sensor Types**: Temperature, humidity, movement, magnetic field, battery monitoring
- **Native Integration**: Full Home Assistant integration with proper device classes
- **Real-time Updates**: Event-driven updates via Bluetooth callbacks
- **Device Management**: Complete control over which devices to monitor
- **Battery Monitoring**: Low battery alerts and voltage monitoring

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/teltonika_eye` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/teltonika_eye/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "Teltonika EYE Sensors" and click to add

5. Configure the scan duration (default: 5 seconds)

### Method 2: HACS Installation

1. Add this repository to HACS as a custom repository
2. Install "Teltonika EYE Sensors" from HACS
3. Restart Home Assistant
4. Add the integration via the UI

## Configuration

### Initial Setup

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Teltonika EYE Sensors"
3. Configure scan duration (1-30 seconds, default: 5)
4. Click "Submit"

### Options

You can modify the scan duration after setup:
1. Go to **Settings** → **Devices & Services**
2. Find "Teltonika EYE Sensors"
3. Click "Configure"
4. Adjust scan duration as needed

## Entities Created

For each discovered Teltonika EYE sensor, the following entities are created:

### Sensors
- `sensor.{device_name}_temperature` - Temperature in °C
- `sensor.{device_name}_humidity` - Relative humidity in %
- `sensor.{device_name}_battery_voltage` - Battery voltage in V
- `sensor.{device_name}_movement_count` - Total movement events
- `sensor.{device_name}_pitch` - Device pitch angle in degrees
- `sensor.{device_name}_roll` - Device roll angle in degrees
- `sensor.{device_name}_rssi` - Bluetooth signal strength in dBm

### Binary Sensors
- `binary_sensor.{device_name}_movement_state` - Movement detection (ON/OFF)
- `binary_sensor.{device_name}_magnetic_field` - Magnetic field detection
- `binary_sensor.{device_name}_low_battery` - Low battery warning

## Device Information

Each sensor appears as a complete device with:
- **Manufacturer**: Teltonika
- **Model**: EYE Sensor
- **Software Version**: Protocol version
- **Identifiers**: Unique device ID based on MAC address

## Automation Examples

### Temperature Alert
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

### Movement Detection
```yaml
automation:
  - alias: "Movement Detected"
    trigger:
      - platform: state
        entity_id: binary_sensor.logikai_2es_movement_state
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.hallway
```

### Low Battery Alert
```yaml
automation:
  - alias: "Sensor Low Battery"
    trigger:
      - platform: state
        entity_id: binary_sensor.logikai_2es_low_battery
        to: 'on'
    action:
      - service: notify.persistent_notification
        data:
          title: "Sensor Battery Low"
          message: "{{ trigger.entity_id }} needs battery replacement"
```

## Dashboard Cards

### Simple Entity Card
```yaml
type: entities
title: Teltonika EYE Sensors
entities:
  - sensor.logikai_2es_temperature
  - sensor.logikai_2es_humidity
  - sensor.logikai_2es_battery_voltage
  - binary_sensor.logikai_2es_movement_state
  - binary_sensor.logikai_2es_low_battery
```

### Temperature Gauge
```yaml
type: gauge
entity: sensor.logikai_2es_temperature
min: 0
max: 50
severity:
  green: 0
  yellow: 25
  red: 35
```

## Troubleshooting

### No Sensors Found
1. Ensure sensors are powered on and in range (< 10 meters)
2. Check Bluetooth permissions:
   ```bash
   sudo usermod -a -G bluetooth homeassistant
   ```
3. Restart Home Assistant after permission changes
4. Try increasing scan duration in integration options

### Integration Won't Load
1. Check Home Assistant logs for errors
2. Ensure `bleak` dependency is installed
3. Verify Bluetooth adapter is working:
   ```bash
   sudo systemctl status bluetooth
   ```

### Entities Not Updating
1. Check if sensors are still in range
2. Verify sensor batteries are not low
3. Check integration logs for scan errors
4. Try reloading the integration

## Technical Details

### Bluetooth Requirements
- Bluetooth LE (Bluetooth 4.0+) adapter required
- Linux: Requires `bluez` and appropriate permissions
- Supported on Home Assistant OS, Supervised, and Container

### Protocol Support
- **Company ID**: 0x089A (Teltonika)
- **Protocol Version**: 0x01
- **Data Structure**: Flag-encoded sensor values
- **Scan Method**: Active BLE scanning

### Performance
- **Scan Interval**: 30 seconds (configurable)
- **Scan Duration**: 5 seconds (configurable 1-30s)
- **Memory Usage**: Minimal
- **CPU Usage**: Very low during scans

## Support

For issues and feature requests:
1. Check Home Assistant logs for errors
2. Verify sensor compatibility with Teltonika EYE protocol
3. Ensure proper Bluetooth setup and permissions

## Version History

- **1.0.0**: Initial release with full sensor support
  - Temperature, humidity, movement, magnetic field sensors
  - Battery monitoring and low battery alerts
  - Configurable scan intervals
  - Native Home Assistant integration