# Teltonika EYE Sensors - Custom Integration Installation

## Quick Installation Guide

### Step 1: Copy Integration Files

Copy the entire `custom_components/teltonika_eye` folder to your Home Assistant configuration directory:

```
/config/custom_components/teltonika_eye/
```

Your directory structure should look like:
```
/config/
├── custom_components/
│   └── teltonika_eye/
│       ├── __init__.py
│       ├── binary_sensor.py
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── manifest.json
│       ├── README.md
│       ├── sensor.py
│       └── translations/
│           └── en.json
└── configuration.yaml
```

### Step 2: Restart Home Assistant

Restart Home Assistant to load the new integration.

### Step 3: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Teltonika EYE Sensors"
4. Click to add the integration
5. Configure scan duration (default: 5 seconds)
6. Click **Submit**

### Step 4: Verify Installation

Your Teltonika EYE sensors should automatically appear as devices with multiple entities:

**Example entities for a sensor named "LogiKal-2ES":**
- `sensor.logikai_2es_temperature`
- `sensor.logikai_2es_humidity`
- `sensor.logikai_2es_battery_voltage`
- `binary_sensor.logikai_2es_movement_state`
- `binary_sensor.logikai_2es_low_battery`

## Features

✅ **Native Integration**: Full Home Assistant integration with proper device classes  
✅ **Auto-Discovery**: Sensors automatically discovered via Bluetooth LE  
✅ **Multiple Sensors**: Supports unlimited sensors simultaneously  
✅ **Real-time Updates**: Configurable scan intervals (default: 30 seconds)  
✅ **Battery Monitoring**: Low battery alerts and voltage monitoring  
✅ **Device Management**: Proper device information and entity organization  
✅ **Configuration UI**: Easy setup through Home Assistant UI  

## Comparison: Custom Integration vs MQTT Bridge

| Feature | Custom Integration | MQTT Bridge |
|---------|-------------------|-------------|
| **Setup Complexity** | Easy (UI-based) | Moderate (requires MQTT) |
| **Dependencies** | None (built-in) | MQTT broker required |
| **Performance** | Native (faster) | Network-dependent |
| **Device Classes** | Perfect integration | Good integration |
| **Configuration** | UI-based | Command-line |
| **Maintenance** | Automatic updates | Manual management |

## Troubleshooting

### Integration Not Found
- Ensure files are in correct directory: `/config/custom_components/teltonika_eye/`
- Restart Home Assistant after copying files
- Check Home Assistant logs for errors

### No Sensors Discovered
- Verify sensors are powered and in range (< 10 meters)
- Check Bluetooth permissions (Linux users)
- Try increasing scan duration in integration options

### Permission Issues (Linux)
```bash
# Add homeassistant user to bluetooth group
sudo usermod -a -G bluetooth homeassistant

# Restart Home Assistant service
sudo systemctl restart home-assistant@homeassistant
```

## Advanced Configuration

### Custom Scan Duration
1. Go to **Settings** → **Devices & Services**
2. Find "Teltonika EYE Sensors" integration
3. Click **Configure**
4. Adjust scan duration (1-30 seconds)
5. Click **Submit**

### Multiple Integrations
You can run multiple instances with different scan durations if needed, though one instance typically handles all sensors in range.

## Support

The custom integration provides the best user experience with:
- Native Home Assistant integration
- Automatic device discovery
- Proper entity management
- UI-based configuration
- Automatic updates with Home Assistant

For most users, this is the recommended installation method over the MQTT bridge.