#pragma once

#include "esphome/components/esp32_ble_tracker/esp32_ble_tracker.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/core/component.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"
#include "esphome/core/automation.h"

#include <map>
#include <string>
#include <vector>

namespace esphome {
namespace teltonika_ble {

static const uint16_t TELTONIKA_COMPANY_ID = 0x089A;
static const uint8_t TELTONIKA_PROTOCOL_VERSION = 0x01;

// Sensor registration structure with templatable MAC addresses
struct SensorRegistration {
  TemplatableValue<std::string> mac_template;
  sensor::Sensor *sensor;
  uint64_t cached_mac{0};
  bool needs_update{true};
};

struct BinarySensorRegistration {
  TemplatableValue<std::string> mac_template;
  binary_sensor::BinarySensor *sensor;
  uint64_t cached_mac{0};
  bool needs_update{true};
};

struct RegisteredSensors {
  std::vector<SensorRegistration> temperature;
  std::vector<SensorRegistration> humidity;
  std::vector<SensorRegistration> movement_count;
  std::vector<SensorRegistration> pitch;
  std::vector<SensorRegistration> roll;
  std::vector<SensorRegistration> battery_voltage;
  std::vector<SensorRegistration> battery_level;
  std::vector<SensorRegistration> rssi;
  
  std::vector<BinarySensorRegistration> movement_state;
  std::vector<BinarySensorRegistration> magnetic_detected;
  std::vector<BinarySensorRegistration> low_battery;
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

  // Sensor registration methods with templatable MAC addresses
  void register_temperature_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.temperature.push_back({mac_template, sens, 0, true});
  }
  void register_humidity_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.humidity.push_back({mac_template, sens, 0, true});
  }
  void register_movement_count_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.movement_count.push_back({mac_template, sens, 0, true});
  }
  void register_pitch_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.pitch.push_back({mac_template, sens, 0, true});
  }
  void register_roll_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.roll.push_back({mac_template, sens, 0, true});
  }
  void register_battery_voltage_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.battery_voltage.push_back({mac_template, sens, 0, true});
  }
  void register_battery_level_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.battery_level.push_back({mac_template, sens, 0, true});
  }
  void register_rssi_sensor(TemplatableValue<std::string> mac_template, sensor::Sensor *sens) {
    registered_sensors_.rssi.push_back({mac_template, sens, 0, true});
  }
  
  void register_movement_sensor(TemplatableValue<std::string> mac_template, binary_sensor::BinarySensor *sens) {
    registered_sensors_.movement_state.push_back({mac_template, sens, 0, true});
  }
  void register_magnetic_sensor(TemplatableValue<std::string> mac_template, binary_sensor::BinarySensor *sens) {
    registered_sensors_.magnetic_detected.push_back({mac_template, sens, 0, true});
  }
  void register_low_battery_sensor(TemplatableValue<std::string> mac_template, binary_sensor::BinarySensor *sens) {
    registered_sensors_.low_battery.push_back({mac_template, sens, 0, true});
  }

 protected:
  void publish_values(uint64_t mac, const TeltonikaCachedValues &values);
  void apply_timeout_logic(uint32_t now_ms);
  void update_mac_addresses();
  uint64_t parse_mac_address(const std::string &mac_str);

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