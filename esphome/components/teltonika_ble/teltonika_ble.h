#pragma once

#include "esphome/components/esp32_ble_tracker/esp32_ble_tracker.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/core/component.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

#include <map>
#include <string>
#include <vector>

namespace esphome {
namespace teltonika_ble {

static const uint16_t TELTONIKA_COMPANY_ID = 0x089A;
static const uint8_t TELTONIKA_PROTOCOL_VERSION = 0x01;

// Sensor registration maps - keyed by MAC address
struct RegisteredSensors {
  std::map<uint64_t, sensor::Sensor *> temperature;
  std::map<uint64_t, sensor::Sensor *> humidity;
  std::map<uint64_t, sensor::Sensor *> movement_count;
  std::map<uint64_t, sensor::Sensor *> pitch;
  std::map<uint64_t, sensor::Sensor *> roll;
  std::map<uint64_t, sensor::Sensor *> battery_voltage;
  std::map<uint64_t, sensor::Sensor *> battery_level;
  std::map<uint64_t, sensor::Sensor *> rssi;
  
  std::map<uint64_t, binary_sensor::BinarySensor *> movement_state;
  std::map<uint64_t, binary_sensor::BinarySensor *> magnetic_detected;
  std::map<uint64_t, binary_sensor::BinarySensor *> low_battery;
};

struct TeltonikaCachedValues {
  float temperature_c{NAN};
  float humidity_percent{NAN};
  uint32_t movement_count{0};
  int8_t pitch_deg{0};
  int16_t roll_deg{0};
  float battery_voltage_v{NAN};
  float battery_level_percent{NAN};
  int8_t rssi_dbm{0};
  bool movement_state{false};
  bool magnetic_detected{false};
  bool low_battery{false};
  uint32_t last_seen_ms{0};
};

class TeltonikaBLEComponent : public Component, public esp32_ble_tracker::ESPBTDeviceListener {
 public:
  TeltonikaBLEComponent();

  void setup() override;
  void loop() override;
  float get_setup_priority() const override { return setup_priority::AFTER_BLUETOOTH; }

  void dump_config() override;

  bool parse_device(const esp32_ble_tracker::ESPBTDevice &device) override;

  void set_discover(bool discover) { this->discover_ = discover; }
  void set_global_timeout(uint32_t seconds) { this->global_timeout_ms_ = seconds * 1000UL; }

  // Sensor registration methods
  void register_temperature_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.temperature[mac] = sens; }
  void register_humidity_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.humidity[mac] = sens; }
  void register_movement_count_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.movement_count[mac] = sens; }
  void register_pitch_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.pitch[mac] = sens; }
  void register_roll_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.roll[mac] = sens; }
  void register_battery_voltage_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.battery_voltage[mac] = sens; }
  void register_battery_level_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.battery_level[mac] = sens; }
  void register_rssi_sensor(uint64_t mac, sensor::Sensor *sens) { registered_sensors_.rssi[mac] = sens; }
  
  void register_movement_sensor(uint64_t mac, binary_sensor::BinarySensor *sens) { registered_sensors_.movement_state[mac] = sens; }
  void register_magnetic_sensor(uint64_t mac, binary_sensor::BinarySensor *sens) { registered_sensors_.magnetic_detected[mac] = sens; }
  void register_low_battery_sensor(uint64_t mac, binary_sensor::BinarySensor *sens) { registered_sensors_.low_battery[mac] = sens; }

 protected:
  void publish_values(uint64_t mac, const TeltonikaCachedValues &values);
  void apply_timeout_logic(uint32_t now_ms);

  bool parse_teltonika_payload(uint64_t mac, const esp32_ble_tracker::ESPBTDevice &device,
                               const std::vector<uint8_t> &payload);

  bool discover_{false};
  uint32_t global_timeout_ms_{300000};
  uint32_t last_scan_ms_{0};

  RegisteredSensors registered_sensors_;
  std::map<uint64_t, TeltonikaCachedValues> cache_;
  std::map<uint64_t, uint32_t> device_timeouts_;
};

}  // namespace teltonika_ble
}  // namespace esphome