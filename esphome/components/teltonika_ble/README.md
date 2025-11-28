# Teltonika EYE BLE Parser for ESPHome (Work‑in‑Progress)

This directory contains an **experimental** ESPHome component that listens for [Teltonika EYE](https://teltonika-gps.com/product/eye-sensor/) BLE advertisements from an ESP32, decodes their manufacturer payload, and publishes the metrics (temperature, humidity, movement, battery state, etc.) as ESPHome sensors. The implementation is still under active development; expect missing features and build errors until the C++ code is completed.

---

## 1. Supported Installation Methods (per the ESPHome “External Components” guidelines)

ESPHome recommends distributing non-core integrations through the [`external_components`](https://esphome.io/components/external_components/) mechanism. The component provided here can be used in either of the standard ways:

### A. Reference a Git repository directly

You can add the GitHub repository as an external component source:

```yaml
external_components:
  - source: github://VignanTej/teltonika-eye-homeassistant@main
    components: [teltonika_ble]
    refresh: 1d
```

* ESPHome will fetch the component from `esphome/components/teltonika_ble/` at compile time.
* You must use ESPHome ≥ 2022.3.0 (external components were added in that release).
* The `refresh: 1d` parameter tells ESPHome to check for updates daily.

### B. Reference a local path (for development/testing)

If you are developing locally or want to modify the component, copy the `esphome/components/teltonika_ble/` directory into your ESPHome config folder and add:

```yaml
external_components:
  - source:
      type: local
      path: components
    components: [teltonika_ble]
```

In this case your project structure should look like:

```
config/esphome/
├─ teltonika_gateway.yaml
├─ components/
│   └─ teltonika_ble/           <- copied from this repo
│       ├─ __init__.py
│       ├─ teltonika_ble.h
│       ├─ teltonika_ble.cpp
│       └─ README.md
└─ secrets.yaml
```

ESPHome will load the component from the local components folder at compile time.

> **Note:** The C++ source currently references ESPHome headers, so although the editor shows include errors, the code will compile once the component is fully implemented and built via the ESPHome build system.

---

## 2. Example ESPHome Configuration

Below is the complete configuration using the new sensor platform approach:

```yaml
esphome:
  name: teltonika-gateway
  friendly_name: Teltonika EYE Gateway

esp32:
  board: esp32dev
  framework:
    type: arduino

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

logger:
  level: DEBUG
  logs:
    teltonika_ble: DEBUG

api:
ota:
web_server:

time:
  - platform: sntp

esp32_ble_tracker:
  scan_parameters:
    interval: 320ms
    window: 30ms
    active: false

external_components:
  - source: github://VignanTej/teltonika-eye-homeassistant
    components: [teltonika_ble]
    refresh: 0s

# Main component configuration
teltonika_ble:
  id: teltonika_ble_component
  discover: true
  timeout: 300s

# Define sensors for each Teltonika device
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

### Configuration Options

**teltonika_ble platform:**
| Option     | Type | Description                                              |
|------------|------|----------------------------------------------------------|
| `id`       | ID   | Component ID to reference in sensor/binary_sensor        |
| `discover` | bool | Auto-detect all Teltonika devices (default: true)        |
| `timeout`  | time | Timeout before marking device unavailable (default: 300s)|

**sensor platform (platform: teltonika_ble):**
| Option               | Type       | Description                                    |
|----------------------|------------|------------------------------------------------|
| `teltonika_ble_id`   | ID         | Reference to teltonika_ble component           |
| `mac_address`        | MAC        | Teltonika device MAC address                   |
| `temperature`        | sensor     | Temperature sensor config (optional)           |
| `humidity`           | sensor     | Humidity sensor config (optional)              |
| `movement_count`     | sensor     | Movement counter sensor config (optional)      |
| `pitch`              | sensor     | Pitch angle sensor config (optional)           |
| `roll`               | sensor     | Roll angle sensor config (optional)            |
| `battery_voltage`    | sensor     | Battery voltage sensor config (optional)       |
| `battery_level`      | sensor     | Battery level % sensor config (optional)       |
| `rssi`               | sensor     | RSSI signal strength sensor config (optional)  |

**binary_sensor platform (platform: teltonika_ble):**
| Option               | Type          | Description                                |
|----------------------|---------------|--------------------------------------------|
| `teltonika_ble_id`   | ID            | Reference to teltonika_ble component       |
| `mac_address`        | MAC           | Teltonika device MAC address               |
| `movement`           | binary_sensor | Movement detection (optional)              |
| `magnetic`           | binary_sensor | Magnetic field detection (optional)        |
| `low_battery`        | binary_sensor | Low battery alert (optional)               |

---

## 3. Current Status - Hardware Tested! 🎉

**✅ Successfully tested with real Teltonika EYE hardware:**
- ✅ Compiles and runs on ESP32
- ✅ Now properly validates Teltonika company ID (0x089A) - **no more false positives!**
- ✅ Detects genuine Teltonika EYE sensors (tested: 7C:D9:F4:13:BD:BF, 7C:D9:F4:14:21:5D)
- ✅ Parses manufacturer data correctly (11-27 byte payloads, protocol v0x01)
- ✅ Extracts all sensor values:
  - Temperature: 27.81-27.88°C ✓
  - Humidity: 63-65% ✓
  - Movement count: 2376-2377 ✓
  - Battery voltage: 3.05-3.06V ✓
  - Battery level: 87.5% ✓
  - RSSI: -46 to -61 dBm ✓
  - Movement detection: ON ✓
- ✅ Multi-device support working
- ✅ Detailed debug logging

**⚠️ Known Issue - Sensors Show "Unknown" in Home Assistant:**
The component successfully parses Teltonika data, but sensors don't appear in HA frontend yet. This requires proper ESPHome sensor platform integration (sensor.py/binary_sensor.py) which is planned for the next update.

**Current Workaround:** Monitor parsed values via ESPHome logs with `logger: level: DEBUG`.

**Recent Fixes:**
- ✅ Fixed false positive detection (validates company ID 0x089A)
- ✅ Added proper manufacturer data validation
- ✅ Improved logging for debugging

---

## 4. Clearing ESPHome Cache (Important!)

If you've previously compiled with an older version of this component, ESPHome caches the external component code. **You must clear the cache** to get the latest version:

**Method 1: Force immediate refresh**
```yaml
external_components:
  - source: github://VignanTej/teltonika-eye-homeassistant@main
    components: [teltonika_ble]
    refresh: 0s  # Force immediate refresh instead of 1d
```

**Method 2: Clear the ESPHome cache directory**

In Home Assistant ESPHome addon, delete the cache:
```bash
# Option A: Via Home Assistant Terminal addon
rm -rf /data/external_components/*

# Option B: Via File Editor or SSH
# Delete folder: /data/external_components/
```

**Method 3: Use a specific commit hash (recommended for stability)**
```yaml
external_components:
  - source: github://VignanTej/teltonika-eye-homeassistant@79746e8
    components: [teltonika_ble]
```
Check https://github.com/VignanTej/teltonika-eye-homeassistant/commits/main for the latest commit hash

After clearing cache or changing the refresh/commit, click "Clean Build Files" in the ESPHome UI before compiling.

---

## 3. Project Status and TODO

The current files are **scaffolding**:

- ✅ Python config schema stub (`__init__.py`).
- ✅ Header and C++ skeleton (`teltonika_ble.h/.cpp`) describing the parser, device cache, and sensor publishing.
- ✅ Base ESPHome YAML and documentation.
- ❌ Core payload parsing is incomplete; many fields are parsed but not yet validated against real sensors.
- ❌ Sensor and binary sensor registration/publishing needs real testing.
- ❌ Auto-discovery vs. manual device handling requires validation.
- ❌ README needs final polish when the component is ready.

**A short-term roadmap:**

1. Finish the C++ parsing logic, especially validation and error handling.
2. Verify multi-device support with real hardware.
3. Ensure timeouts and availability markers work.
4. Add any additional configuration options (e.g., filter by device name).
5. Document final usage examples and troubleshooting tips.

---

## 4. Troubleshooting & Notes

- **IncludePath warnings in VSCode**  
  These occur because the files are edited outside the ESPHome compilation environment. They disappear during actual ESPHome builds.

- **Active scanning**  
  If advertisements are missed, set `active: true` for `esp32_ble_tracker`. This trades power for quicker detections.

- **Battery level heuristic**  
  The current code estimates battery percentage from the reported voltage (2000–3200 mV range). Adjust as needed.

- **Security**  
  Teltonika EYE advertisements are broadcast/plaintext; no BLE pairing is required.

---

## 5. Contributing

Contributions are welcome! Focus areas include:

- Completing and validating the C++ parser.
- Adding unit tests or simulations.
- Improving the README based on real-world usage.
- Benchmarks for BLE scanning performance.

Please file issues or submit PRs in the main repository.

---

**License:** Inherit the repository root `LICENSE`.

Once the component is stable and released, this README should be updated with final configuration samples and support information. Until then, treat the code as experimental and subject to change. Happy hacking!