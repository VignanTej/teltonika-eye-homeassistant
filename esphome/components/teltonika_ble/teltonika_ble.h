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

struct TeltonikaDeviceConfig {
  esp32_ble_tracker::ESPBTDeviceAddress mac_address;
  optional<uint32_t> timeout_ms;
  std::string name;
  bool enable_rssi{true};
  bool enable_battery_level{true};
};

struct TeltonikaSensorSet {
  sensor::Sensor *temperature{nullptr};
  sensor::Sensor *humidity{nullptr};
  sensor::Sensor *movement_count{nullptr};
  sensor::Sensor *pitch{nullptr};
  sensor::Sensor *roll{nullptr};
  sensor::Sensor *battery_voltage{nullptr};
  sensor::Sensor *battery_level{nullptr};
  sensor::Sensor *rssi{nullptr};

  binary_sensor::BinarySensor *movement_state{nullptr};
  binary_sensor::BinarySensor *magnetic_detected{nullptr};
  binary_sensor::BinarySensor *low_battery{nullptr};
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
  void set_global_scan_interval(uint32_t seconds) { this->scan_interval_ms_ = seconds * 1000UL; }
  void set_global_timeout(uint32_t seconds) { this->global_timeout_ms_ = seconds * 1000UL; }
  void set_global_rssi_enabled(bool enabled) { this->global_rssi_enabled_ = enabled; }
  void set_global_battery_level_enabled(bool enabled) { this->global_battery_level_enabled_ = enabled; }

  void add_device_config(const TeltonikaDeviceConfig &cfg);

 protected:
  TeltonikaSensorSet &get_or_create_sensor_set(const std::string &key, const std::string &name, const TeltonikaDeviceConfig *cfg);
  TeltonikaSensorSet &create_sensor_entities(const std::string &key, const std::string &name, const TeltonikaDeviceConfig *cfg);

  void publish_values(const std::string &key, const TeltonikaSensorSet &sensors, const TeltonikaCachedValues &values);
  void apply_timeout_logic(uint32_t now_ms);

  bool parse_teltonika_payload(const std::string &key, const TeltonikaDeviceConfig *cfg,
                               const esp32_ble_tracker::ESPBTDevice &device,
                               const std::vector<uint8_t> &payload);

  optional<TeltonikaDeviceConfig> find_device_config(const esp32_ble_tracker::ESPBTDeviceAddress &mac) const;
  std::string make_device_key(const esp32_ble_tracker::ESPBTDeviceAddress &mac) const;
  std::string make_device_name(const std::string &configured_name, const std::string &mac_str) const;

  bool discover_{false};
  uint32_t scan_interval_ms_{60000};  // default 60s
  uint32_t global_timeout_ms_{300000};
  bool global_rssi_enabled_{true};
  bool global_battery_level_enabled_{true};

  uint32_t last_scan_ms_{0};

  std::vector<TeltonikaDeviceConfig> configured_devices_;

  std::map<std::string, TeltonikaSensorSet> sensors_;
  std::map<std::string, TeltonikaCachedValues> cache_;
  std::map<std::string, uint32_t> device_timeouts_;
};

}  // namespace teltonika_ble
}  // namespace esphome