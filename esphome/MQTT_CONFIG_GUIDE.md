# MQTT Configuration Guide

## Overview

The Teltonika Gateway now includes MQTT support with UI-configurable settings. MQTT broker, username, and password can be viewed and edited through Home Assistant or the ESPHome Web UI.

## Configuration Fields

Four configuration entities are available for MQTT configuration:

| Field | Type | Description | Default Value |
|-------|------|-------------|---------------|
| **MQTT Broker** | Text | Hostname or IP address of your MQTT broker | `homeassistant.local` |
| **MQTT Port** | Number | Port number for MQTT connection | `1883` |
| **MQTT Username** | Text | Username for MQTT authentication | `mqtt_user` |
| **MQTT Password** | Text | Password for MQTT authentication (hidden) | `mqtt_password` |

**Standard MQTT Ports:**
- **1883** - Standard MQTT (unencrypted)
- **8883** - MQTT over TLS (encrypted)

## How to Configure

### Via Home Assistant UI

1. Open Home Assistant
2. Go to **Settings** → **Devices & Services**
3. Find "Tez Teltonika EYE Gateway"
4. Click on the device
5. Scroll to the **Configuration** section
6. Edit:
   - MQTT Broker
   - MQTT Username
   - MQTT Password

### Via ESPHome Web UI

1. Open `http://[device-ip]` in your browser
2. Find the configuration fields (text and number inputs)
3. Update the MQTT settings:
   - Broker hostname/IP
   - Port number (1883 for standard, 8883 for TLS)
   - Username
   - Password
4. Values are saved automatically to device flash

## Important Limitation - Recompilation Required

**⚠️ MQTT CONNECTION PARAMETERS ARE SET AT COMPILE TIME**

Due to ESPHome architecture limitations:
- Changing MQTT settings in the UI **updates the stored values**
- However, the **active MQTT connection uses compile-time values**
- You **must recompile and upload** new firmware for changes to take effect

### Why This Limitation Exists

ESPHome's MQTT component:
1. Reads configuration during firmware compilation
2. Establishes connection during `setup()` phase
3. Cannot dynamically reconfigure the connection at runtime

The text entities provide a convenient way to:
- ✅ Store your MQTT credentials on the device
- ✅ View current settings in HA/Web UI
- ✅ Edit settings without modifying YAML
- ❌ But require recompilation to activate new settings

## Step-by-Step: Changing MQTT Settings

### Step 1: Update Settings in UI
1. Open Home Assistant or Web UI
2. Edit **MQTT Broker**, **MQTT Port**, **Username**, **Password**
3. New values are saved to device flash memory

### Step 2: Trigger Recompilation
You have two options:

**Option A: ESPHome Dashboard**
1. Open ESPHome dashboard
2. Click "Install" on your gateway device
3. Choose "Wirelessly" or "Plug into serial port"
4. Wait for compilation and upload
5. Device reboots with new MQTT settings

**Option B: Home Assistant ESP Home Integration**
1. In ESPHome dashboard, click "Edit" on your device
2. Make any minor change (e.g., add a comment)
3. Click "Save"
4. Click "Install"
5. New firmware is compiled with updated MQTT values

### Step 3: Verify Connection
After reboot, check logs:
```
[mqtt] Connected to MQTT broker
```

## MQTT Topics

Once connected, the gateway publishes to these topics:

### Topic Prefix

The MQTT topic prefix uses the device name with MAC address suffix for uniqueness:
- Format: `tez-teltonika-gateway-XXXXXX` (where XXXXXX is the last 6 chars of MAC)
- This ensures each gateway has unique topics when you have multiple gateways

### Status Topics
- `tez-teltonika-gateway-XXXXXX/status` - Online/Offline status
- `tez-teltonika-gateway-XXXXXX/debug` - Debug messages

### Sensor Topics (per device)
- `tez-teltonika-gateway-XXXXXX/sensor/teltonika_eye_1_temperature/state`
- `tez-teltonika-gateway-XXXXXX/sensor/teltonika_eye_1_humidity/state`
- `tez-teltonika-gateway-XXXXXX/sensor/teltonika_eye_1_battery_level/state`
- `tez-teltonika-gateway-XXXXXX/sensor/teltonika_eye_1_rssi/state`
- And so on for all configured sensors...

### Binary Sensor Topics
- `tez-teltonika-gateway-XXXXXX/binary_sensor/teltonika_eye_1_movement/state`
- `tez-teltonika-gateway-XXXXXX/binary_sensor/teltonika_eye_1_magnetic_field/state`
- `tez-teltonika-gateway-XXXXXX/binary_sensor/teltonika_eye_1_low_battery/state`

### Text Sensor Topics
- `tez-teltonika-gateway-XXXXXX/text_sensor/teltonika_devices_discovered/state`

## Advanced: Direct MQTT Configuration

If you prefer to hardcode MQTT settings (no UI configuration):

```yaml
mqtt:
  broker: "192.168.1.100"
  username: "my_mqtt_user"
  password: "my_secure_password"
  port: 1883
  discovery: true
```

## Troubleshooting

### "MQTT not connecting after UI change"
→ **Solution**: Recompile and upload new firmware

### "Credentials show in logs"
→ Add to logger exclusions:
```yaml
logger:
  level: INFO
  logs:
    mqtt: WARN  # Don't log MQTT details
```

### "Want to disable MQTT"
→ Comment out the entire `mqtt:` block in YAML

### "Need different MQTT port"
→ Edit YAML, change `port:` value (default is 1883 for MQTT, 8883 for MQTT/TLS)

## Security Considerations

### Password Security
- MQTT password is stored in flash memory
- Shown as `password` type in UI (hidden dots)
- Transmitted in plain text over network (unless using MQTT/TLS)

### Recommendations
1. Use strong MQTT passwords
2. Consider MQTT over TLS for sensitive environments
3. Restrict MQTT broker access by IP/network
4. Use a dedicated MQTT user with minimal permissions

### MQTT Over TLS
For encrypted MQTT connections:

```yaml
mqtt:
  broker: "secure-broker.example.com"
  port: 8883
  username: !lambda return id(mqtt_username_text).state.c_str();
  password: !lambda return id(mqtt_password_text).state.c_str();
  ssl_fingerprints:
    - "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD"
```

## Integration with Home Assistant

Home Assistant automatically discovers MQTT devices when:
- `discovery: true` is set (default)
- Home Assistant has MQTT integration configured
- Both are connected to the same MQTT broker

Entities appear in:
- **Settings** → **Devices & Services** → **MQTT**
- Look for "Tez Teltonika EYE Gateway"

---

## Alternative: Full Runtime Reconfiguration

For true runtime MQTT reconfiguration without recompilation, consider:

1. **Use Home Assistant MQTT Integration** - Let HA handle MQTT
2. **Dedicated MQTT Bridge Device** - Separate ESP32 as MQTT gateway
3. **Custom Component** - Write C++ component with runtime reconfiguration (advanced)

However, the current UI-configurable approach provides a good balance between:
- ✅ Easy credential management
- ✅ Visible in HA and Web UI
- ⚠️ Requires one-time recompilation after changes