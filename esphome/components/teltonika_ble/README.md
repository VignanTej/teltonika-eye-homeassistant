# Teltonika EYE BLE Parser for ESPHome (Work‑in‑Progress)

This directory contains an **experimental** ESPHome component that listens for [Teltonika EYE](https://teltonika-gps.com/product/eye-sensor/) BLE advertisements from an ESP32, decodes their manufacturer payload, and publishes the metrics (temperature, humidity, movement, battery state, etc.) as ESPHome sensors. The implementation is still under active development; expect missing features and build errors until the C++ code is completed.

---

## 1. Supported Installation Methods (per the ESPHome “External Components” guidelines)

ESPHome recommends distributing non-core integrations through the [`external_components`](https://esphome.io/components/external_components/) mechanism. The component provided here can be used in either of the standard ways:

### A. Reference a Git repository directly

Once the code works end‑to‑end, you will be able to add the GitHub repository as an external component source:

```yaml
external_components:
  - source: github://<your-user>/teltonika-eye-homeassistant/esphome
    components: [teltonika_ble]
```

* Replace `<your-user>` with the actual GitHub owner once the repository is public.
* ESPHome will fetch the `esphome/teltonika_ble/` folder at compile time.
* You must use ESPHome ≥ 2022.3.0 (external components were added in that release).

### B. Reference a local path (recommended for local development)

If you are prototyping locally or running ESPHome inside Home Assistant, copy the `esphome/teltonika_ble/` directory into your ESPHome project and add:

```yaml
external_components:
  - source:
      type: local
      path: teltonika_ble
    components: [teltonika_ble]
```

In this case your project structure may look like:

```
config/
└─ esphome/
   ├─ teltonika_gateway.yaml
   ├─ teltonika_ble/            <- copied from this repo
   │   ├─ __init__.py
   │   ├─ teltonika_ble.h
   │   ├─ teltonika_ble.cpp
   │   └─ README.md
   └─ secrets.yaml
```

ESPHome will load the component from the local folder at compile time, mirroring the behavior documented in the external components guide.

> **Note:** The C++ source currently references ESPHome headers, so although the editor shows include errors, the code will compile once the component is fully implemented and built via the ESPHome build system.

---

## 2. Example ESPHome Node Configuration

Below is a starter YAML (`teltonika_gateway.yaml`) that demonstrates the expected structure. You can adapt the values for your environment.

```yaml
esphome:
  name: teltonika_gateway
  comment: ESP32 gateway for Teltonika EYE BLE sensors

esp32:
  board: esp32dev
  framework:
    type: arduino

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  ap:
    ssid: "Teltonika Fallback Hotspot"
    password: "changeme123"

captive_portal:

logger:
  level: INFO

api:
ota:

web_server:
  port: 80

time:
  - platform: sntp
    id: sntp_time

esp32_ble_tracker:
  scan_parameters:
    interval: 320ms
    window: 30ms
    active: false

external_components:
  - source:
      type: local
      path: teltonika_ble          # or github://... when published
    components: [teltonika_ble]

teltonika_ble:
  discover: true
  scan_interval: 60s
  timeout: 300s
  rssi: true
  battery_level: true

  devices:
    - mac_address: "AA:BB:CC:DD:EE:FF"
      name: "office_eye"
      timeout: 600s
      rssi: true
      battery_level: true
    - mac_address: "11:22:33:44:55:66"
      name: "warehouse_eye"
```

### Device-Level Options

| Option            | Type    | Description                                                                           |
|-------------------|---------|---------------------------------------------------------------------------------------|
| `discover`        | bool    | Auto-create sensors for any Teltonika device in range.                               |
| `devices`         | list    | Explicit list of Teltonika sensors to monitor.                                       |
| `scan_interval`   | time    | BLE rescanning interval. Default `60s`.                                              |
| `timeout`         | time    | Global timeout before marking the device unavailable.                                |
| `rssi`            | bool    | Create RSSI sensors for all devices (overridable per device).                        |
| `battery_level`   | bool    | Create estimated battery-level sensors (overridable per device).                     |
| `mac_address`     | string  | Device MAC (required per device).                                                    |
| `name`            | string  | Friendly name used as the sensor prefix; optional (defaults to `Teltonika_<MAC>`).  |
| Per-device `timeout`, `rssi`, `battery_level` | overrides | Override the global defaults on a per-device basis. |

**Entity Naming:** Each device yields sensors/binary sensors using `<name>_<measurement>` (e.g., `office_eye_temperature`, `office_eye_movement`, `warehouse_eye_battery_voltage`, etc.).

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