# Teltonika EYE Sensors for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

_Integration to integrate with [Teltonika EYE Sensors][teltonika_eye] via Bluetooth LE._

**This integration provides two deployment options:**
1. **Home Assistant Custom Integration** - Direct BLE integration with Home Assistant
2. **ESPHome Gateway** - ESP32-based BLE-to-MQTT bridge for extended range

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Temperature, humidity, battery voltage, movement count, orientation sensors
`binary_sensor` | Movement detection, magnetic field detection, low battery alerts

## Features

- 🌡️ **Temperature Monitoring** - Real-time temperature readings in °C
- 💧 **Humidity Monitoring** - Relative humidity percentage
- 🔋 **Battery Monitoring** - Voltage monitoring and low battery alerts
- 🚶 **Movement Detection** - Motion detection and event counting
- 🧲 **Magnetic Field Detection** - Magnetic field presence detection
- 📐 **Orientation Sensors** - Pitch and roll angle measurements
- 📶 **Signal Strength** - Bluetooth RSSI monitoring
- 🔄 **Auto-Discovery** - Automatic sensor discovery via Bluetooth LE
- ⚙️ **Easy Configuration** - UI-based setup (or ESPHome for gateway option)
- 🌐 **ESPHome Gateway Option** - ESP32 BLE-to-MQTT bridge for extended coverage

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/your-username/teltonika-eye-homeassistant`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Teltonika EYE Sensors" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
2. If you do not have a `custom_components` directory (folder) there, you need to create it
3. In the `custom_components` directory (folder) create a new folder called `teltonika_eye`
4. Download _all_ the files from the `custom_components/teltonika_eye/` directory (folder) in this repository
5. Place the files you downloaded in the new directory (folder) you created
6. Restart Home Assistant

## Configuration

### Option 1: Home Assistant Direct Integration

1. In the HA UI go to "Settings" -> "Devices & Services"
2. Click "Add Integration"
3. Search for "Teltonika EYE Sensors"
4. Follow the configuration steps:
   - Set scan duration (1-30 seconds, default: 5)
   - Click "Submit"

### Option 2: ESPHome Gateway (Recommended for Extended Range)

For better range and reliability, use an ESP32 as a BLE-to-MQTT gateway:

1. See the [ESPHome Gateway Documentation](esphome/MQTT_CONFIG_GUIDE.md) for complete setup instructions
2. Configure MQTT broker details in `esphome/secrets.yaml`
3. Flash the gateway firmware to an ESP32 device
4. Sensors will auto-discover in Home Assistant via MQTT

**Benefits of ESPHome Gateway:**
- Extend BLE range with strategically placed ESP32 devices
- Lower power consumption on Home Assistant server
- More reliable BLE scanning with dedicated hardware
- Support for up to 5 Teltonika EYE sensors per gateway
- Visual WiFi/API status indication via onboard LED (GPIO2)

**WiFi Status LED Indicators:**
- **Fast Pulse** (250ms) - WiFi disconnected, attempting to connect
- **Slow Pulse** (500ms) - WiFi connected, waiting for Home Assistant API
- **Solid ON** - Fully connected (WiFi + Home Assistant API)
- **OFF** - Initial boot or error state

## Entities

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

## Example Automations

### Temperature Alert
```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.teltonika_eye_temperature
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
        entity_id: binary_sensor.teltonika_eye_movement_state
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.hallway
```

## Requirements

- Home Assistant 2023.1.0 or newer
- Bluetooth LE adapter (Bluetooth 4.0+)
- Teltonika EYE sensors with BLE advertising enabled

### Linux Requirements
- `bluez` package installed
- User permissions for Bluetooth access:
  ```bash
  sudo usermod -a -G bluetooth homeassistant
  ```

## Troubleshooting

### No Sensors Found
1. Ensure sensors are powered on and in range (< 10 meters)
2. Check Bluetooth permissions (Linux users)
3. Verify sensors are advertising (not in sleep mode)
4. Try increasing scan duration in integration options

### Integration Won't Load
1. Check Home Assistant logs for errors
2. Ensure `bleak` dependency is installed
3. Verify Bluetooth adapter is working
4. Restart Home Assistant after installation

## Supported Devices

This integration supports Teltonika EYE sensors that use the Teltonika BLE protocol:
- Company ID: 0x089A
- Protocol Version: 0x01
- All sensor variants (temperature, humidity, movement, magnetic field)

## Contributing

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

**Developer**: Vignan Tej
**Company**: Tez Solutions
**License**: MIT License

This integration was developed independently to provide seamless integration between Teltonika EYE sensors and Home Assistant.

Special thanks to the Home Assistant community and the developers of the `bleak` library for Bluetooth LE support.

---

[integration_blueprint]: https://github.com/ludeeus/integration_blueprint
[teltonika_eye]: https://teltonika-gps.com/
[commits-shield]: https://img.shields.io/github/commit-activity/y/vignantej/teltonika-eye-homeassistant.svg?style=for-the-badge
[commits]: https://github.com/vignantej/teltonika-eye-homeassistant/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/vignantej/teltonika-eye-homeassistant.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/vignantej/teltonika-eye-homeassistant.svg?style=for-the-badge
[releases]: https://github.com/vignantej/teltonika-eye-homeassistant/releases