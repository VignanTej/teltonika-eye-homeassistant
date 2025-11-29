# BLE Distance Tracking Configuration Guide

This guide explains how to configure iBeacon, Eddystone, and Teltonika sensor distance tracking in ESPHome.

## Overview

The ESP32 can track the approximate distance to BLE devices using RSSI (Received Signal Strength Indicator) measurements. This works with:
- **Teltonika EYE** sensors (already configured in your setup)
- **iBeacons** (Apple's beacon standard)
- **Eddystone** beacons (Google's beacon standard)
- **Generic BLE devices** (any BLE device broadcasting)

## How Distance Calculation Works

Distance is estimated using the path loss formula:

```
d = 10^((TxPower - RSSI) / (10 * n))
```

Where:
- `d` = Distance in meters
- `TxPower` = Transmit power at 1 meter (device-specific, in dBm)
- `RSSI` = Received signal strength (measured by ESP32, in dBm)
- `n` = Path loss exponent (2.0 for free space, 2.5-4.0 for indoor environments)

## Configuration Steps

### 1. Find Your Beacon MAC Addresses

Use ESPHome logs to discover nearby BLE devices:

```yaml
logger:
  level: DEBUG
  logs:
    esp32_ble_tracker: DEBUG
```

Compile and upload, then check the logs for MAC addresses and signal strengths.

### 2. Add RSSI Sensors

For each beacon you want to track, add a `ble_rssi` sensor:

```yaml
sensor:
  # For iBeacons
  - platform: ble_rssi
    mac_address: "AA:BB:CC:DD:EE:FF"  # Replace with your beacon's MAC
    name: "My iBeacon RSSI"
    id: my_ibeacon_rssi

  # For Eddystone beacons
  - platform: ble_rssi
    mac_address: "11:22:33:44:55:66"  # Replace with your beacon's MAC
    name: "My Eddystone RSSI"
    id: my_eddystone_rssi
```

### 3. Add Distance Calculation Templates

Create template sensors to convert RSSI to distance:

#### For iBeacons:
```yaml
sensor:
  - platform: template
    name: "iBeacon Distance"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    lambda: |-
      float rssi = id(my_ibeacon_rssi).state;
      if (isnan(rssi) || rssi == 0) return {};
      
      // Calibration values - ADJUST THESE!
      float txPower = -59.0;  // Typical for iBeacon
      float pathLoss = 2.0;   // 2.0 = free space, 2.5-4.0 = indoor
      
      float distance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
      return distance;
    update_interval: 2s
```

#### For Eddystone Beacons:
```yaml
sensor:
  - platform: template
    name: "Eddystone Distance"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    lambda: |-
      float rssi = id(my_eddystone_rssi).state;
      if (isnan(rssi) || rssi == 0) return {};
      
      // Eddystone beacons often broadcast their TxPower
      // Check your beacon's specifications or calibrate
      float txPower = -20.0;  // ADJUST THIS!
      float pathLoss = 2.5;   // Indoor environment
      
      float distance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
      return distance;
    update_interval: 2s
```

#### For Teltonika EYE Sensors:
```yaml
sensor:
  - platform: template
    name: "Teltonika EYE 1 Distance"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    lambda: |-
      // Use the RSSI from the teltonika_ble platform
      float rssi = id(eye1_rssi_sensor).state;  // Reference your RSSI sensor ID
      if (isnan(rssi) || rssi == 0) return {};
      
      float txPower = -59.0;  // Teltonika EYE typical
      float pathLoss = 2.0;
      
      float distance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
      return distance;
    update_interval: 5s
```

## Calibration Guide

### Step 1: Determine TxPower

1. Place the beacon exactly 1 meter from your ESP32
2. Observe the RSSI value in Home Assistant
3. Use this RSSI as your `txPower` value

Example:
- At 1 meter, RSSI = -65 dBm
- Set `txPower = -65.0` in your template

### Step 2: Calibrate Path Loss Exponent

1. Place beacon at known distances (1m, 2m, 3m, 5m)
2. Record actual distance vs. calculated distance
3. Adjust `pathLoss` value until calculated matches actual

Common values:
- **2.0**: Free space (outdoors, clear line of sight)
- **2.5**: Office environment (some obstacles)
- **3.0**: Dense indoor (walls, furniture)
- **4.0**: Very cluttered (metal objects, thick walls)

### Step 3: Fine-Tune with Environmental Factor

For more accuracy, add an environmental calibration factor:

```yaml
lambda: |-
  float rssi = id(my_beacon_rssi).state;
  if (isnan(rssi) || rssi == 0) return {};
  
  float txPower = -59.0;
  float pathLoss = 2.5;
  float envFactor = 0.89;  // Calibration multiplier
  
  float rawDistance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
  float distance = rawDistance * envFactor;
  return distance;
```

## Distance Accuracy

Keep these limitations in mind:

| Range | Typical Accuracy |
|-------|------------------|
| 0-2m  | ±0.5m |
| 2-5m  | ±1.0m |
| 5-10m | ±2.0m |
| >10m  | ±3.0m+ |

Factors affecting accuracy:
- Physical obstacles (walls, furniture)
- WiFi/Bluetooth interference
- Beacon orientation
- Human bodies blocking signal
- Metal objects nearby

## Advanced: Smoothing RSSI Values

RSSI fluctuates significantly. Apply filtering for more stable distance readings:

```yaml
sensor:
  - platform: template
    name: "Beacon Distance (Smoothed)"
    unit_of_measurement: "m"
    accuracy_decimals: 1
    icon: "mdi:signal-distance-variant"
    filters:
      - exponential_moving_average:
          alpha: 0.1  # Lower = smoother but slower response
          send_every: 3  # Update every 3 measurements
    lambda: |-
      float rssi = id(my_beacon_rssi).state;
      if (isnan(rssi) || rssi == 0) return {};
      
      float txPower = -59.0;
      float pathLoss = 2.5;
      
      float distance = pow(10.0, ((txPower) - rssi) / (10.0 * pathLoss));
      return distance;
    update_interval: 1s
```

## Example: Proximity Zones

Use distance data to create proximity zones:

```yaml
binary_sensor:
  - platform: template
    name: "Beacon in Near Zone"
    lambda: |-
      float dist = id(beacon_distance).state;
      return !isnan(dist) && dist < 2.0;  // Less than 2 meters

  - platform: template
    name: "Beacon in Medium Zone"
    lambda: |-
      float dist = id(beacon_distance).state;
      return !isnan(dist) && dist >= 2.0 && dist < 5.0;

  - platform: template
    name: "Beacon in Far Zone"
    lambda: |-
      float dist = id(beacon_distance).state;
      return !isnan(dist) && dist >= 5.0;
```

## Troubleshooting

### Distance shows "unknown"
- Check that RSSI sensor has valid readings (not 0 or NaN)
- Verify beacon is in range and broadcasting
- Check beacon battery level

### Distance very inaccurate
- Recalibrate `txPower` at 1 meter
- Adjust `pathLoss` for your environment
- Add RSSI smoothing filter
- Check for interference sources

### Distance jumps around
- Normal behavior due to signal fluctuations
- Apply exponential_moving_average filter
- Increase `alpha` value for more smoothing
- Update less frequently (increase `update_interval`)

## Complete Example Configuration

See `teltonika_gateway.yaml` for a complete working example with:
- 5 Teltonika EYE sensors with distance tracking
- 2 iBeacon devices with distance tracking
- 2 Eddystone beacons with distance tracking
- Proximity zone binary sensors
- Smoothed distance calculations

---

**Note:** Distance estimation via RSSI is approximate. For critical applications requiring precise measurements, consider using UWB (Ultra-Wideband) technology instead.