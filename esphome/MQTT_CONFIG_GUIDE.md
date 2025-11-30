# MQTT Configuration Guide

## Overview

The Teltonika Gateway includes MQTT support for publishing sensor data to your MQTT broker. MQTT credentials are configured statically in YAML using the `secrets.yaml` file. Changes to MQTT settings require recompiling and reflashing the firmware.

**Note:** As of the latest version, runtime MQTT configuration via the web UI has been removed to ensure compilation stability. All MQTT settings must be configured in `secrets.yaml` before compilation.

## Quick Setup

### Step 1: Create secrets.yaml

Copy the example file:
```bash
cp esphome/secrets.yaml.example esphome/secrets.yaml
```

### Step 2: Edit Your Credentials

Edit `esphome/secrets.yaml` with your actual MQTT broker details:

```yaml
# MQTT Configuration
mqtt_broker: "192.168.1.100"    # Your MQTT broker IP or hostname
mqtt_port: 1883                  # Standard MQTT port
mqtt_username: "your_username"
mqtt_password: "your_password"
```

### Step 3: Compile and Upload

The MQTT configuration is compiled into the firmware. Upload the firmware to your ESP32.

## Configuration Reference

### MQTT Settings in teltonika_gateway.yaml

```yaml
mqtt:
  broker: !secret mqtt_broker
  port: !secret mqtt_port
  username: !secret mqtt_username
  password: !secret mqtt_password
  discovery: true
  discovery_retain: true
  topic_prefix: "esphome"
  on_connect:
    - logger.log: "Connected to MQTT broker"
  on_disconnect:
    - logger.log: "Disconnected from MQTT broker"
```

### Standard MQTT Ports

- **1883** - Standard MQTT (unencrypted)
- **8883** - MQTT over TLS (encrypted, requires SSL configuration)

## MQTT Topics

### Topic Prefix

The MQTT topic prefix is set to `"esphome"` by default. This can be changed in the YAML configuration if needed. The device publishes under this prefix with its unique device name.

### Published Topics

**Status:**
- `tez-teltonika-gateway-XXXXXX/status` - `online`/`offline`

**Sensors (per device):**
- `.../sensor/teltonika_eye_1_temperature/state`
- `.../sensor/teltonika_eye_1_humidity/state`
- `.../sensor/teltonika_eye_1_battery_level/state`
- `.../sensor/teltonika_eye_1_battery_voltage/state`
- `.../sensor/teltonika_eye_1_movement_count/state`
- `.../sensor/teltonika_eye_1_pitch/state`
- `.../sensor/teltonika_eye_1_roll/state`
- `.../sensor/teltonika_eye_1_rssi/state`

**Binary Sensors:**
- `.../binary_sensor/teltonika_eye_1_movement/state`
- `.../binary_sensor/teltonika_eye_1_magnetic_field/state`
- `.../binary_sensor/teltonika_eye_1_low_battery/state`

**Text Sensors:**
- `.../text_sensor/teltonika_devices_discovered/state`
- `.../text_sensor/gateway_ip/state`
- `.../text_sensor/gateway_mac/state`

## Home Assistant Integration

### Auto-Discovery

MQTT auto-discovery is enabled by default. Devices will automatically appear in Home Assistant:

1. Ensure your Home Assistant has MQTT integration configured
2. Both HA and the gateway must connect to same MQTT broker
3. Devices appear in: **Settings** → **Devices & Services** → **MQTT**
4. Look for "Tez Teltonika EYE Gateway"

### Manual Topic Subscription

If auto-discovery isn't working, manually subscribe to topics:

```yaml
# configuration.yaml
mqtt:
  sensor:
    - name: "EYE 1 Temperature"
      state_topic: "tez-teltonika-gateway-XXXXXX/sensor/teltonika_eye_1_temperature/state"
      unit_of_measurement: "°C"
      device_class: temperature
```

## Security

### Protecting MQTT Credentials

The `secrets.yaml` file should be added to `.gitignore`:

```bash
# In your .gitignore
esphome/secrets.yaml
```

This prevents accidentally committing credentials to version control.

### MQTT Over TLS

For encrypted MQTT connections, update your configuration:

```yaml
mqtt:
  broker: !secret mqtt_broker
  port: 8883
  username: !secret mqtt_username
  password: !secret mqtt_password
  ssl_fingerprints:
    - "AA BB CC DD EE FF 00 11 22 33 44 55 66 77 88 99 AA BB CC DD"
```

Get the SSL fingerprint from your MQTT broker:
```bash
openssl s_client -connect mqtt.example.com:8883 < /dev/null 2>/dev/null | \
  openssl x509 -fingerprint -noout
```

## Troubleshooting

### MQTT Not Connecting

**Check broker is reachable:**
```bash
ping your-mqtt-broker-ip
```

**Verify credentials:**
- Double-check `secrets.yaml` for typos
- Ensure MQTT user has publish permissions
- Check MQTT broker logs for authentication failures

**Check ESPHome logs:**
```
[mqtt] Connecting to MQTT...
[mqtt] Connected to MQTT broker
```

If you see connection failures, verify:
- Broker IP/hostname is correct
- Port is correct (1883 for standard MQTT)
- Username and password are valid

### Auto-Discovery Not Working

1. **Verify HA MQTT integration is set up:**
   - Settings → Devices & Services → MQTT
   - Should show "Configured"

2. **Check MQTT topic prefix:**
   - Look in ESPHome logs for actual topic prefix used
   - Verify HA is subscribed to `homeassistant/#`

3. **Force re-discovery:**
   - Restart ESPHome device
   - Check HA: Settings → Devices & Services → MQTT → Configure
   - Look for new devices

### Changing MQTT Configuration

MQTT settings are compiled into the firmware. To change them:

1. Edit `esphome/secrets.yaml` with new credentials
2. Click "Install" in ESPHome dashboard
3. Firmware recompiles with new configuration
4. Upload to device (OTA or USB)
5. Device reboots with updated MQTT settings

**Important:** There is no runtime MQTT configuration UI. All changes must be made before compilation.

## Alternative: Hardcoded Configuration

If you don't want to use `secrets.yaml`, you can hardcode values in the YAML:

```yaml
mqtt:
  broker: "192.168.1.100"
  port: 1883
  username: "mqtt_user"
  password: "mqtt_password"
  discovery: true
```

**Note:** This is less secure as credentials are visible in YAML file.

## Testing MQTT Connection

Use MQTT Explorer or command-line tools to verify topics:

### Using mosquitto_sub

```bash
# Subscribe to all topics
mosquitto_sub -h your-broker-ip -u mqtt_user -P mqtt_password -t '#' -v

# Subscribe to specific device
mosquitto_sub -h your-broker-ip -u mqtt_user -P mqtt_password \
  -t 'tez-teltonika-gateway-+/sensor/+/state' -v
```

### Using MQTT Explorer

1. Download MQTT Explorer
2. Connect to your broker
3. Navigate to `tez-teltonika-gateway-XXXXXX/`
4. Verify topics are being published

---

**Summary:**
- MQTT credentials go in `secrets.yaml` (keeps them private)
- Changes require recompilation and reflashing (static configuration)
- No runtime configuration UI - all settings are compiled into firmware
- Auto-discovery makes integration with Home Assistant seamless
- Use the ESPHome web dashboard or CLI to update and flash firmware