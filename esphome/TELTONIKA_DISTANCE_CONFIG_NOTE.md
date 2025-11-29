# Important: Configuring Distance Sensors for Teltonika EYE Devices

## Current Limitation

The Teltonika BLE component's RSSI sensors are defined within the platform configuration but don't expose individual sensor IDs that can be referenced by template sensors for distance calculation.

## Workaround Solution

To enable distance calculations for Teltonika EYE devices, you need to assign IDs to the RSSI sensors:

### Step 1: Add IDs to RSSI Sensors

Modify your sensor configuration to include IDs:

```yaml
sensor:
  - platform: teltonika_ble
    teltonika_ble_id: teltonika_ble_component
    mac_address: !lambda |-
      return id(eye1_mac_text).state.c_str();
    rssi:
      name: "Teltonika EYE 1 RSSI"
      id: eye1_rssi  # ADD THIS ID
```

### Step 2: Update Distance Template Sensors

Then reference these IDs in the distance calculation templates:

```yaml
sensor:
  - platform: template
    name: "Teltonika EYE 1 Distance"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    lambda: |-
      float rssi = id(eye1_rssi).state;  # Reference the ID
      if (isnan(rssi) || rssi == 0) return {};
      
      // Teltonika EYE calibration
      float txPower = -59.0;  // Typical for Teltonika EYE
      float pathLoss = 2.0;   // Adjust for your environment
      
      float distance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
      return distance;
    update_interval: 5s
```

### Complete Example for One Device

```yaml
sensor:
  # Teltonika EYE sensor with RSSI
  - platform: teltonika_ble
    teltonika_ble_id: teltonika_ble_component
    mac_address: !lambda |-
      return id(eye1_mac_text).state.c_str();
    temperature:
      name: "Teltonika EYE 1 Temperature"
    humidity:
      name: "Teltonika EYE 1 Humidity"
    rssi:
      name: "Teltonika EYE 1 RSSI"
      id: eye1_rssi  # Important: Add ID here

  # Distance calculation template
  - platform: template
    name: "Teltonika EYE 1 Distance"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    lambda: |-
      float rssi = id(eye1_rssi).state;
      if (isnan(rssi) || rssi == 0) return {};
      float distance = pow(10.0, ((-59.0) - rssi) / (10.0 * 2.0));
      return distance;
    update_interval: 5s
```

## Calibrating Distance for Your Environment

1. **Measure TxPower**: Place sensor 1 meter away, note RSSI value, use as txPower
2. **Adjust Path Loss**: 
   - 2.0 for outdoors/clear line of sight
   - 2.5 for office environments
   - 3.0-4.0 for dense indoor spaces with walls

## Alternative: Use BLE RSSI Platform

If you prefer not to use the Teltonika platform's RSSI sensor, you can track any BLE device (including Teltonika) using the generic ble_rssi platform:

```yaml
sensor:
  # Direct RSSI tracking (works even without teltonika_ble sensors)
  - platform: ble_rssi
    mac_address: "7C:D9:F4:13:BD:BF"  # Your Teltonika MAC
    name: "Teltonika EYE 1 RSSI Alt"
    id: eye1_rssi_alt

  # Distance from this RSSI
  - platform: template
    name: "Teltonika EYE 1 Distance Alt"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    lambda: |-
      float rssi = id(eye1_rssi_alt).state;
      if (isnan(rssi) || rssi == 0) return {};
      float distance = pow(10.0, ((-59.0) - rssi) / (10.0 * 2.0));
      return distance;
    update_interval: 2s
```

This approach:
- ✅ Works independently of teltonika_ble platform
- ✅ Can track any BLE device by MAC address
- ✅ Simpler ID management
- ❌ Doesn't provide Teltonika-specific sensor data (temp, humidity, etc.)