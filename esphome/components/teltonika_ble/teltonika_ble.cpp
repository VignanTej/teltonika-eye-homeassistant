#include "teltonika_ble.h"

namespace esphome {
namespace teltonika_ble {

static const char *const TAG = "teltonika_ble";

TeltonikaBLEComponent::TeltonikaBLEComponent() = default;

void TeltonikaBLEComponent::setup() {
  ESP_LOGCONFIG(TAG, "Setting up Teltonika BLE component");
  this->last_scan_ms_ = millis();
}

void TeltonikaBLEComponent::loop() {
  uint32_t now = millis();

  if (now - this->last_scan_ms_ >= this->scan_interval_ms_) {
    this->last_scan_ms_ = now;
  }

  this->apply_timeout_logic(now);
}

void TeltonikaBLEComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "Teltonika BLE:");
  ESP_LOGCONFIG(TAG, "  Discover devices: %s", YESNO(this->discover_));
  ESP_LOGCONFIG(TAG, "  Scan interval: %u ms", this->scan_interval_ms_);
  ESP_LOGCONFIG(TAG, "  Global timeout: %u ms", this->global_timeout_ms_);
  ESP_LOGCONFIG(TAG, "  RSSI sensor enabled by default: %s", YESNO(this->global_rssi_enabled_));
  ESP_LOGCONFIG(TAG, "  Battery level sensor enabled by default: %s", YESNO(this->global_battery_level_enabled_));
  ESP_LOGCONFIG(TAG, "  Configured devices: %u", this->configured_devices_.size());

  for (const auto &cfg : this->configured_devices_) {
    char mac_str[18];
    sprintf(mac_str, "%02X:%02X:%02X:%02X:%02X:%02X",
            (uint8_t)((cfg.mac_address >> 40) & 0xFF),
            (uint8_t)((cfg.mac_address >> 32) & 0xFF),
            (uint8_t)((cfg.mac_address >> 24) & 0xFF),
            (uint8_t)((cfg.mac_address >> 16) & 0xFF),
            (uint8_t)((cfg.mac_address >> 8) & 0xFF),
            (uint8_t)(cfg.mac_address & 0xFF));
    ESP_LOGCONFIG(TAG, "    - Device %s (%s)", cfg.name.empty() ? mac_str : cfg.name.c_str(), mac_str);
    ESP_LOGCONFIG(TAG, "      Timeout: %u ms", cfg.timeout_ms > 0 ? cfg.timeout_ms : this->global_timeout_ms_);
    ESP_LOGCONFIG(TAG, "      RSSI sensor enabled: %s", YESNO(cfg.enable_rssi));
    ESP_LOGCONFIG(TAG, "      Battery level sensor enabled: %s", YESNO(cfg.enable_battery_level));
  }
}

void TeltonikaBLEComponent::add_device(uint64_t mac, const std::string &name, uint32_t timeout_ms,
                                       bool enable_rssi, bool enable_battery_level) {
  TeltonikaDeviceConfig cfg;
  cfg.mac_address = mac;
  cfg.name = name;
  cfg.timeout_ms = timeout_ms;
  cfg.enable_rssi = enable_rssi;
  cfg.enable_battery_level = enable_battery_level;
  this->configured_devices_.push_back(cfg);
}

TeltonikaSensorSet &TeltonikaBLEComponent::get_or_create_sensor_set(const std::string &key, const std::string &name,
                                                                    const TeltonikaDeviceConfig *cfg) {
  auto it = this->sensors_.find(key);
  if (it != this->sensors_.end()) {
    return it->second;
  }
  return this->create_sensor_entities(key, name, cfg);
}

TeltonikaSensorSet &TeltonikaBLEComponent::create_sensor_entities(const std::string &key, const std::string &name,
                                                                  const TeltonikaDeviceConfig *cfg) {
  TeltonikaSensorSet sensors;

  auto make_sensor = [&](const char *suffix) -> sensor::Sensor * {
    auto sensor_obj = new sensor::Sensor();
    std::string full_name = name + " " + suffix;
    sensor_obj->set_name(full_name.c_str());
    return sensor_obj;
  };

  auto make_binary = [&](const char *suffix) -> binary_sensor::BinarySensor * {
    auto bs = new binary_sensor::BinarySensor();
    std::string full_name = name + " " + suffix;
    bs->set_name(full_name.c_str());
    return bs;
  };

  sensors.temperature = make_sensor("Temperature");
  sensors.humidity = make_sensor("Humidity");
  sensors.movement_count = make_sensor("Movement Count");
  sensors.pitch = make_sensor("Pitch");
  sensors.roll = make_sensor("Roll");
  sensors.battery_voltage = make_sensor("Battery Voltage");

  bool enable_battery_level = cfg ? cfg->enable_battery_level : this->global_battery_level_enabled_;
  if (enable_battery_level) {
    sensors.battery_level = make_sensor("Battery Level");
  }

  bool enable_rssi = cfg ? cfg->enable_rssi : this->global_rssi_enabled_;
  if (enable_rssi) {
    sensors.rssi = make_sensor("RSSI");
  }

  sensors.movement_state = make_binary("Movement");
  sensors.magnetic_detected = make_binary("Magnetic Field");
  sensors.low_battery = make_binary("Low Battery");

  this->sensors_[key] = sensors;
  return this->sensors_[key];
}

bool TeltonikaBLEComponent::parse_device(const esp32_ble_tracker::ESPBTDevice &device) {
  // Get manufacturer data as ServiceData vector
  auto manu_datas = device.get_manufacturer_datas();
  
  // ESPHome stores manufacturer data as ServiceData
  // We need to iterate and find Teltonika company ID
  bool found_teltonika = false;
  std::vector<uint8_t> payload;
  
  for (const auto &manu : manu_datas) {
    // ServiceData has uuid (ESPBTUUID) and data (vector<uint8_t>)
    // For manufacturer specific data, the company ID is embedded differently
    // Let's check the data payload directly - Teltonika data starts with protocol version 0x01
    if (manu.data.size() >= 2 && manu.data[0] == TELTONIKA_PROTOCOL_VERSION) {
      // This looks like Teltonika data
      payload = manu.data;
      found_teltonika = true;
      break;
    }
  }
  
  if (!found_teltonika) {
    return false;
  }

  auto mac = device.address_uint64();
  auto device_cfg = this->find_device_config(mac);

  if (!this->discover_ && !device_cfg.has_value()) {
    return false;
  }

  char mac_str[18];
  sprintf(mac_str, "%02X:%02X:%02X:%02X:%02X:%02X",
          (uint8_t)((mac >> 40) & 0xFF),
          (uint8_t)((mac >> 32) & 0xFF),
          (uint8_t)((mac >> 24) & 0xFF),
          (uint8_t)((mac >> 16) & 0xFF),
          (uint8_t)((mac >> 8) & 0xFF),
          (uint8_t)(mac & 0xFF));
  
  std::string key(mac_str);
  std::string name = this->make_device_name(device_cfg.has_value() ? device_cfg->name : "", key);

  if (!this->parse_teltonika_payload(key, device_cfg.has_value() ? &(*device_cfg) : nullptr, device, payload)) {
    ESP_LOGW(TAG, "Failed to parse payload for Teltonika device %s", key.c_str());
    return false;
  }

  return true;
}

optional<TeltonikaDeviceConfig> TeltonikaBLEComponent::find_device_config(uint64_t mac) const {
  for (const auto &cfg : this->configured_devices_) {
    if (cfg.mac_address == mac) {
      return cfg;
    }
  }
  return {};
}

std::string TeltonikaBLEComponent::make_device_name(const std::string &configured_name, const std::string &mac_str) const {
  if (!configured_name.empty()) {
    return configured_name;
  }
  std::string suffix = mac_str;
  std::replace(suffix.begin(), suffix.end(), ':', '_');
  return "Teltonika_" + suffix;
}

bool TeltonikaBLEComponent::parse_teltonika_payload(const std::string &key, const TeltonikaDeviceConfig *cfg,
                                                    const esp32_ble_tracker::ESPBTDevice &device,
                                                    const std::vector<uint8_t> &payload) {
  if (payload.size() < 2) {
    ESP_LOGW(TAG, "[%s] Manufacturer data too short (%u bytes)", key.c_str(), payload.size());
    return false;
  }

  uint8_t protocol_version = payload[0];
  if (protocol_version != TELTONIKA_PROTOCOL_VERSION) {
    ESP_LOGW(TAG, "[%s] Unsupported Teltonika protocol version 0x%02X", key.c_str(), protocol_version);
    return false;
  }

  uint8_t flags = payload[1];
  TeltonikaSensorSet &sensor_set = this->get_or_create_sensor_set(key, this->make_device_name(cfg ? cfg->name : "", key), cfg);
  TeltonikaCachedValues &cached = this->cache_[key];
  cached.last_seen_ms = millis();

  size_t offset = 2;

  auto read_u8 = [&](uint8_t &out) -> bool {
    if (offset + 1 > payload.size())
      return false;
    out = payload[offset++];
    return true;
  };

  auto read_u16_be = [&](uint16_t &out) -> bool {
    if (offset + 2 > payload.size())
      return false;
    out = ((uint16_t) payload[offset] << 8) | payload[offset + 1];
    offset += 2;
    return true;
  };

  auto read_i8 = [&](int8_t &out) -> bool {
    if (offset + 1 > payload.size())
      return false;
    out = static_cast<int8_t>(payload[offset++]);
    return true;
  };

  auto read_i16_be = [&](int16_t &out) -> bool {
    if (offset + 2 > payload.size())
      return false;
    out = (int16_t)(((uint16_t) payload[offset] << 8) | payload[offset + 1]);
    offset += 2;
    return true;
  };

  if (flags & (1 << 0)) {
    uint16_t raw;
    if (read_u16_be(raw)) {
      cached.temperature_c = raw / 100.0f;
    }
  }

  if (flags & (1 << 1)) {
    uint8_t raw;
    if (read_u8(raw)) {
      cached.humidity_percent = raw;
    }
  }

  if (flags & (1 << 4)) {
    uint16_t raw;
    if (read_u16_be(raw)) {
      cached.movement_state = (raw & 0x8000) != 0;
      cached.movement_count = raw & 0x7FFF;
    }
  }

  if (flags & (1 << 5)) {
    int8_t pitch;
    int16_t roll;
    if (read_i8(pitch) && read_i16_be(roll)) {
      cached.pitch_deg = pitch;
      cached.roll_deg = roll;
    }
  }

  cached.magnetic_detected = (flags & (1 << 3)) != 0;
  cached.low_battery = (flags & (1 << 6)) != 0;

  if (flags & (1 << 7)) {
    uint8_t raw;
    if (read_u8(raw)) {
      float mv = 2000.0f + raw * 10.0f;
      cached.battery_voltage_v = mv / 1000.0f;
      cached.battery_level_percent = std::min(std::max((mv - 2000.0f) / (3200.0f - 2000.0f) * 100.0f, 0.0f), 100.0f);
    }
  }

  cached.rssi_dbm = device.get_rssi();

  this->publish_values(key, sensor_set, cached);
  this->device_timeouts_[key] = cached.last_seen_ms;
  return true;
}

void TeltonikaBLEComponent::publish_values(const std::string &key, const TeltonikaSensorSet &sensors,
                                           const TeltonikaCachedValues &values) {
  auto publish = [](sensor::Sensor *sensor_ptr, float value) {
    if (sensor_ptr != nullptr && !std::isnan(value)) {
      sensor_ptr->publish_state(value);
    }
  };

  publish(sensors.temperature, values.temperature_c);
  publish(sensors.humidity, values.humidity_percent);
  publish(sensors.movement_count, values.movement_count);
  publish(sensors.pitch, values.pitch_deg);
  publish(sensors.roll, values.roll_deg);
  publish(sensors.battery_voltage, values.battery_voltage_v);
  publish(sensors.battery_level, values.battery_level_percent);
  publish(sensors.rssi, values.rssi_dbm);

  if (sensors.movement_state != nullptr)
    sensors.movement_state->publish_state(values.movement_state);
  if (sensors.magnetic_detected != nullptr)
    sensors.magnetic_detected->publish_state(values.magnetic_detected);
  if (sensors.low_battery != nullptr)
    sensors.low_battery->publish_state(values.low_battery);

  ESP_LOGD(TAG, "[%s] Published Teltonika data", key.c_str());
}

void TeltonikaBLEComponent::apply_timeout_logic(uint32_t now_ms) {
  for (auto &entry : this->sensors_) {
    const std::string &key = entry.first;
    auto timeout_it = this->device_timeouts_.find(key);
    if (timeout_it == this->device_timeouts_.end())
      continue;

    uint32_t last_seen = timeout_it->second;
    uint32_t timeout_ms = this->global_timeout_ms_;

    // Check for device-specific timeout
    for (const auto &device_cfg : this->configured_devices_) {
      char mac_str[18];
      sprintf(mac_str, "%02X:%02X:%02X:%02X:%02X:%02X",
              (uint8_t)((device_cfg.mac_address >> 40) & 0xFF),
              (uint8_t)((device_cfg.mac_address >> 32) & 0xFF),
              (uint8_t)((device_cfg.mac_address >> 24) & 0xFF),
              (uint8_t)((device_cfg.mac_address >> 16) & 0xFF),
              (uint8_t)((device_cfg.mac_address >> 8) & 0xFF),
              (uint8_t)(device_cfg.mac_address & 0xFF));
      
      if (key == std::string(mac_str)) {
        if (device_cfg.timeout_ms > 0) {
          timeout_ms = device_cfg.timeout_ms;
        }
        break;
      }
    }

    if (now_ms - last_seen > timeout_ms) {
      TeltonikaSensorSet &sensors = entry.second;
      if (sensors.temperature != nullptr)
        sensors.temperature->publish_state(NAN);
      if (sensors.humidity != nullptr)
        sensors.humidity->publish_state(NAN);
      if (sensors.movement_count != nullptr)
        sensors.movement_count->publish_state(NAN);
      if (sensors.pitch != nullptr)
        sensors.pitch->publish_state(NAN);
      if (sensors.roll != nullptr)
        sensors.roll->publish_state(NAN);
      if (sensors.battery_voltage != nullptr)
        sensors.battery_voltage->publish_state(NAN);
      if (sensors.battery_level != nullptr)
        sensors.battery_level->publish_state(NAN);
      if (sensors.rssi != nullptr)
        sensors.rssi->publish_state(NAN);

      if (sensors.movement_state != nullptr)
        sensors.movement_state->publish_state(false);
      if (sensors.magnetic_detected != nullptr)
        sensors.magnetic_detected->publish_state(false);
      if (sensors.low_battery != nullptr)
        sensors.low_battery->publish_state(false);

      this->device_timeouts_.erase(timeout_it);
      ESP_LOGW(TAG, "[%s] Device timeout reached, set sensors to unavailable", key.c_str());
    }
  }
}

}  // namespace teltonika_ble
}  // namespace esphome