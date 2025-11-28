# Implementation Plan: Fix Teltonika BLE Component Issues

## Current Issues

### Issue 1: False Positive Detection
**Problem:** Non-Teltonika devices (e.g., 3B:BB:8A:40:BC:85) are being detected as Teltonika sensors
**Root Cause:** Only checking protocol version byte (0x01), not validating actual Teltonika company ID

### Issue 2: Sensors Show "Unknown" in Home Assistant
**Problem:** All sensors show "Unknown" state despite successful data parsing
**Root Cause:** Dynamically created C++ sensors aren't registered with ESPHome's sensor platform

## Solution Overview

### Part 1: Fix False Positive Detection

**Changes needed in `teltonika_ble.cpp`:**
1. Properly extract and validate Teltonika company ID (0x089A) from manufacturer data
2. Add validation for minimum payload size (must be at least 2 bytes)
3. Add validation for flags byte (should be reasonable value, not random)
4. Only accept devices that pass all validations

**Code changes:**
```cpp
bool TeltonikaBLEComponent::parse_device(...) {
  // Extract company ID from ServiceData UUID field
  // ESPHome stores company ID in the uuid field
  for (const auto &manu : manu_datas) {
    // Get company ID from UUID (may be in uuid16 or first 2 bytes of uuid128)
    uint16_t company_id = /* extract from manu.uuid */;
    
    if (company_id != TELTONIKA_COMPANY_ID) {
      continue; // Not Teltonika
    }
    
    // Now validate protocol and payload
    if (payload.size() < 2 || payload[0] != TELTONIKA_PROTOCOL_VERSION) {
      continue;
    }
    
    // This is a valid Teltonika device
    ...
  }
}
```

### Part 2: Create Proper Sensor Platform

**New file: `sensor.py`**
- Define sensor platform that allows users to specify sensors per MAC address
- Register sensor objects with the C++ component
- Each sensor type (temperature, humidity, etc.) is optional

**New file: `binary_sensor.py`**
- Define binary sensor platform (movement, magnetic, low_battery)
- Register with C++ component

**Modified: `teltonika_ble.h`**
Add methods to register sensors:
```cpp
void register_temperature_sensor(const std::string &mac, sensor::Sensor *sens);
void register_humidity_sensor(const std::string &mac, sensor::Sensor *sens);
// ... etc for all sensor types
```

**Modified: `teltonika_ble.cpp`**
- Remove dynamic sensor creation
- Store registered sensors in maps (keyed by MAC address)
- In `publish_values()`, publish to registered sensors only
```cpp
std::map<std::string, sensor::Sensor*> temperature_sensors_;
std::map<std::string, sensor::Sensor*> humidity_sensors_;
// etc.
```

**Modified: `__init__.py`**
- Remove old device registration code
- Export `CONF_TELTONIKA_BLE_ID` for sensor platforms to reference parent component
- Simplify to just set global options

### Part 3: Update YAML Syntax

**New YAML structure:**
```yaml
teltonika_ble:
  id: teltonika_ble_component
  discover: true

sensor:
  - platform: teltonika_ble
    teltonika_ble_id: teltonika_ble_component
    mac_address: "7C:D9:F4:13:BD:BF"
    temperature:
      name: "Teltonika EYE 1 Temperature"
    humidity:
      name: "Teltonika EYE 1 Humidity"
    movement_count:
      name: "Teltonika EYE 1 Movement Count"
    pitch:
      name: "Teltonika EYE 1 Pitch"
    roll:
      name: "Teltonika EYE 1 Roll"
    battery_voltage:
      name: "Teltonika EYE 1 Battery Voltage"
    battery_level:
      name: "Teltonika EYE 1 Battery Level"
    rssi:
      name: "Teltonika EYE 1 RSSI"

  - platform: teltonika_ble
    teltonika_ble_id: teltonika_ble_component
    mac_address: "7C:D9:F4:14:21:5D"
    temperature:
      name: "Teltonika EYE 2 Temperature"
    # ... etc

binary_sensor:
  - platform: teltonika_ble
    teltonika_ble_id: teltonika_ble_component
    mac_address: "7C:D9:F4:13:BD:BF"
    movement:
      name: "Teltonika EYE 1 Movement"
    magnetic:
      name: "Teltonika EYE 1 Magnetic Field"
    low_battery:
      name: "Teltonika EYE 1 Low Battery"
```

## Implementation Order

1. ✅ Create `sensor.py` platform file
2. Create `binary_sensor.py` platform file
3. Update `teltonika_ble.h` with sensor registration methods
4. Update `teltonika_ble.cpp`:
   - Fix false positive detection
   - Add sensor registration methods
   - Remove dynamic sensor creation
   - Use registered sensors in publish_values()
5. Update `__init__.py` - simplify and export CONF_TELTONIKA_BLE_ID
6. Update `teltonika_gateway.yaml` with new syntax for both devices
7. Update README with new configuration format
8. Test, commit, and push to GitHub

## Expected Outcome

After implementation:
- ✅ No false positives (only actual Teltonika devices detected)
- ✅ All sensors appear in Home Assistant with proper names
- ✅ Values update correctly
- ✅ Multi-device support maintained
- ✅ Cleaner YAML configuration

Would you like me to proceed with this implementation?