#include "teltonika_ble.h"

namespace esphome {
namespace teltonika_ble {

static const char *const TAG = "teltonika_ble";

TeltonikaBLEComponent::TeltonikaBLEComponent() = default;

void TeltonikaBLEComponent::setup() {
  ESP_LOGI(TAG, "Setting up Teltonika BLE component...");
  ESP_LOGI(TAG, "Discover mode: %s", this->discover_ ? "enabled" : "disabled");
  this->update_mac_addresses();
  this->last_scan_ms_ = millis();
  ESP_LOGI(TAG, "Teltonika BLE component setup complete");
}

void TeltonikaBLEComponent::loop() {
  uint32_t now = millis();
  this->update_mac_addresses();
  this->apply_timeout_logic(now);
}

void TeltonikaBLEComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "Teltonika BLE:");
  ESP_LOGCONFIG(TAG, "  Discover devices: %s", YESNO(this->discover_));
  ESP_LOGCONFIG(TAG, "  Global timeout: %u ms", this->global_timeout_ms_);
  int sensor_count = this->registered_sensors_.temperature.size() +
                     this->registered_sensors_.humidity.size() +
                     this->registered_sensors_.movement_count.size() +
                     this->registered_sensors_.pitch.size() +
                     this->registered_sensors_.roll.size() +
                     this->registered_sensors_.battery_voltage.size() +
                     this->registered_sensors_.battery_level.size() +
                     this->registered_sensors_.rssi.size() +
                     this->registered_sensors_.movement_state.size() +
                     this->registered_sensors_.magnetic_detected.size() +
                     this->registered_sensors_.low_battery.size();
  ESP_LOGCONFIG(TAG, "  Registered sensors: %d", sensor_count);
}

bool TeltonikaBLEComponent::parse_device(const esp32_ble_tracker::ESPBTDevice &device) {
  ESP_LOGV(TAG, "parse_device called for %s", device.address_str().c_str());
  
  // Get manufacturer data
  auto manu_datas = device.get_manufacturer_datas();
  
  if (manu_datas.empty()) {
    return false;
  }
  
  // Find Teltonika manufacturer data by company ID
  bool found_teltonika = false;
  std::vector<uint8_t> payload;
  
  for (const auto &manu : manu_datas) {
    // In ESPHome, the UUID for manufacturer data contains the company ID
    // esp_bt_uuid_t has len and uuid fields
    auto uuid = manu.uuid.get_uuid();
    uint16_t company_id = 0;
    
    // Extract 16-bit company ID from UUID based on length
    if (uuid.len == ESP_UUID_LEN_16) {
      // 16-bit UUID - company ID is in the uuid union
      company_id = uuid.uuid.uuid16;
    } else if (uuid.len == ESP_UUID_LEN_128) {
      // 128-bit UUID - company ID is in first 2 bytes (little endian)
      company_id = uuid.uuid.uuid128[0] | (uuid.uuid.uuid128[1] << 8);
    } else if (uuid.len == ESP_UUID_LEN_32) {
      // 32-bit UUID - company ID in lower 16 bits
      company_id = uuid.uuid.uuid32 & 0xFFFF;
    } else {
      ESP_LOGV(TAG, "Unexpected UUID length: %d", uuid.len);
      continue;
    }
    
    ESP_LOGV(TAG, "Manufacturer data company ID: 0x%04X, size: %d", company_id, manu.data.size());
    
    // Check if this is Teltonika (company ID 0x089A)
    if (company_id != TELTONIKA_COMPANY_ID) {
      continue;
    }
    
    // Validate payload
    if (manu.data.size() < 2) {
      ESP_LOGW(TAG, "Teltonika device %s has insufficient data (%d bytes)", 
               device.address_str().c_str(), manu.data.size());
      continue;
    }
    
    // Validate protocol version
    if (manu.data[0] != TELTONIKA_PROTOCOL_VERSION) {
      ESP_LOGW(TAG, "Teltonika device %s has unsupported protocol v0x%02X", 
               device.address_str().c_str(), manu.data[0]);
      continue;
    }
    
    // This is a valid Teltonika device
    ESP_LOGI(TAG, "Found Teltonika device %s (company ID: 0x%04X, protocol: 0x%02X)", 
             device.address_str().c_str(), company_id, manu.data[0]);
    payload = manu.data;
    found_teltonika = true;
    break;
  }
  
  if (!found_teltonika) {
    return false;
  }

  uint64_t mac = device.address_uint64();
  
  // Check if we have any sensors registered for this device
  auto has_mac_registered = [mac](const auto &registrations) {
    for (const auto &reg : registrations) {
      if (reg.cached_mac == mac) return true;
    }
    return false;
  };
  
  bool has_sensors = has_mac_registered(this->registered_sensors_.temperature) ||
                     has_mac_registered(this->registered_sensors_.humidity) ||
                     has_mac_registered(this->registered_sensors_.movement_count) ||
                     has_mac_registered(this->registered_sensors_.pitch) ||
                     has_mac_registered(this->registered_sensors_.roll) ||
                     has_mac_registered(this->registered_sensors_.battery_voltage) ||
                     has_mac_registered(this->registered_sensors_.battery_level) ||
                     has_mac_registered(this->registered_sensors_.rssi) ||
                     has_mac_registered(this->registered_sensors_.movement_state) ||
                     has_mac_registered(this->registered_sensors_.magnetic_detected) ||
                     has_mac_registered(this->registered_sensors_.low_battery);

  if (!this->discover_ && !has_sensors) {
    ESP_LOGV(TAG, "Device %s not configured, skipping", device.address_str().c_str());
    return false;
  }

  if (!this->parse_teltonika_payload(mac, device, payload)) {
    ESP_LOGW(TAG, "Failed to parse payload for Teltonika device %s", device.address_str().c_str());
    return false;
  }

  return true;
}

bool TeltonikaBLEComponent::parse_teltonika_payload(uint64_t mac,
                                                    const esp32_ble_tracker::ESPBTDevice &device,
                                                    const std::vector<uint8_t> &payload) {
  if (payload.size() < 2) {
    return false;
  }

  uint8_t protocol_version = payload[0];
  if (protocol_version != TELTONIKA_PROTOCOL_VERSION) {
    return false;
  }

  uint8_t flags = payload[1];
  TeltonikaCachedValues &cached = this->cache_[mac];
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

  // Parse temperature
  if (flags & (1 << 0)) {
    uint16_t raw;
    if (read_u16_be(raw)) {
      cached.temperature_c = raw / 100.0f;
    }
  }

  // Parse humidity
  if (flags & (1 << 1)) {
    uint8_t raw;
    if (read_u8(raw)) {
      cached.humidity_percent = raw;
    }
  }

  // Parse movement
  if (flags & (1 << 4)) {
    uint16_t raw;
    if (read_u16_be(raw)) {
      cached.movement_state = (raw & 0x8000) != 0;
      cached.movement_count = raw & 0x7FFF;
    }
  }

  // Parse angles
  if (flags & (1 << 5)) {
    int8_t pitch;
    int16_t roll;
    if (read_i8(pitch) && read_i16_be(roll)) {
      cached.pitch_deg = pitch;
      cached.roll_deg = roll;
    }
  }

  // Parse magnetic sensor (inverted: 0 = detected, 1 = not detected)
  cached.magnetic_detected = (flags & (1 << 3)) == 0;
  
  // Parse low battery
  cached.low_battery = (flags & (1 << 6)) != 0;

  // Parse battery voltage
  if (flags & (1 << 7)) {
    uint8_t raw;
    if (read_u8(raw)) {
      float mv = 2000.0f + raw * 10.0f;
      cached.battery_voltage_v = mv / 1000.0f;
      cached.battery_level_percent = std::min(std::max((mv - 2000.0f) / (3200.0f - 2000.0f) * 100.0f, 0.0f), 100.0f);
    }
  }

  // Store RSSI
  cached.rssi_dbm = device.get_rssi();

  // Publish to registered sensors
  this->publish_values(mac, cached);
  this->device_timeouts_[mac] = cached.last_seen_ms;
  
  return true;
}

void TeltonikaBLEComponent::publish_values(uint64_t mac, const TeltonikaCachedValues &values) {
  auto publish = [](sensor::Sensor *sensor_ptr, float value) {
    if (sensor_ptr != nullptr && !std::isnan(value)) {
      sensor_ptr->publish_state(value);
    }
  };
  
  auto publish_binary = [](binary_sensor::BinarySensor *sensor_ptr, bool value) {
    if (sensor_ptr != nullptr) {
      sensor_ptr->publish_state(value);
    }
  };

  // Helper to publish to matching sensor registrations
  auto publish_to_matching = [mac](const auto &registrations, auto publish_func, auto value) {
    for (const auto &reg : registrations) {
      if (reg.cached_mac == mac) {
        publish_func(reg.sensor, value);
      }
    }
  };

  // Publish all sensor values if registered
  publish_to_matching(this->registered_sensors_.temperature, publish, values.temperature_c);
  publish_to_matching(this->registered_sensors_.humidity, publish, values.humidity_percent);
  publish_to_matching(this->registered_sensors_.movement_count, publish, (float)values.movement_count);
  publish_to_matching(this->registered_sensors_.pitch, publish, (float)values.pitch_deg);
  publish_to_matching(this->registered_sensors_.roll, publish, (float)values.roll_deg);
  publish_to_matching(this->registered_sensors_.battery_voltage, publish, values.battery_voltage_v);
  publish_to_matching(this->registered_sensors_.battery_level, publish, values.battery_level_percent);
  publish_to_matching(this->registered_sensors_.rssi, publish, (float)values.rssi_dbm);
  
  // Publish binary sensors
  publish_to_matching(this->registered_sensors_.movement_state, publish_binary, values.movement_state);
  publish_to_matching(this->registered_sensors_.magnetic_detected, publish_binary, values.magnetic_detected);
  publish_to_matching(this->registered_sensors_.low_battery, publish_binary, values.low_battery);

  ESP_LOGD(TAG, "[%02X:%02X:%02X:%02X:%02X:%02X] Published Teltonika data",
           (uint8_t)((mac >> 40) & 0xFF),
           (uint8_t)((mac >> 32) & 0xFF),
           (uint8_t)((mac >> 24) & 0xFF),
           (uint8_t)((mac >> 16) & 0xFF),
           (uint8_t)((mac >> 8) & 0xFF),
           (uint8_t)(mac & 0xFF));
}

void TeltonikaBLEComponent::apply_timeout_logic(uint32_t now_ms) {
  std::vector<uint64_t> to_timeout;
  
  for (auto &entry : this->device_timeouts_) {
    uint64_t mac = entry.first;
    uint32_t last_seen = entry.second;
    
    if (now_ms - last_seen > this->global_timeout_ms_) {
      to_timeout.push_back(mac);
    }
  }
  
  // Clear timed-out devices
  for (uint64_t mac : to_timeout) {
    ESP_LOGW(TAG, "Device timeout, clearing values");
    
    // Helper to clear matching sensor registrations
    auto clear_matching_sensors = [mac](const auto &registrations) {
      for (const auto &reg : registrations) {
        if (reg.cached_mac == mac && reg.sensor != nullptr) {
          reg.sensor->publish_state(NAN);
        }
      }
    };
    
    auto clear_matching_binary = [mac](const auto &registrations) {
      for (const auto &reg : registrations) {
        if (reg.cached_mac == mac && reg.sensor != nullptr) {
          reg.sensor->publish_state(false);
        }
      }
    };
    
    // Clear all sensor types
    clear_matching_sensors(this->registered_sensors_.temperature);
    clear_matching_sensors(this->registered_sensors_.humidity);
    clear_matching_sensors(this->registered_sensors_.movement_count);
    clear_matching_sensors(this->registered_sensors_.pitch);
    clear_matching_sensors(this->registered_sensors_.roll);
    clear_matching_sensors(this->registered_sensors_.battery_voltage);
    clear_matching_sensors(this->registered_sensors_.battery_level);
    clear_matching_sensors(this->registered_sensors_.rssi);
    
    // Clear binary sensors
    clear_matching_binary(this->registered_sensors_.movement_state);
    clear_matching_binary(this->registered_sensors_.magnetic_detected);
    clear_matching_binary(this->registered_sensors_.low_battery);
    
    this->device_timeouts_.erase(mac);
    this->cache_.erase(mac);
  }
}

void TeltonikaBLEComponent::update_mac_addresses() {
  // Update all sensor registrations
  auto update_registrations = [](auto &registrations) {
    for (auto &reg : registrations) {
      if (reg.mac_template.has_value()) {
        auto mac_str = reg.mac_template.value();
        if (!mac_str.empty()) {
          // Parse MAC address string to uint64
          uint64_t new_mac = 0;
          if (sscanf(mac_str.c_str(), "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
                     (uint8_t*)&new_mac + 5,
                     (uint8_t*)&new_mac + 4,
                     (uint8_t*)&new_mac + 3,
                     (uint8_t*)&new_mac + 2,
                     (uint8_t*)&new_mac + 1,
                     (uint8_t*)&new_mac) == 6) {
            // Reconstruct MAC in correct byte order
            uint64_t parsed_mac = 0;
            parsed_mac  = ((uint64_t)*((uint8_t*)&new_mac + 5)) << 40;
            parsed_mac |= ((uint64_t)*((uint8_t*)&new_mac + 4)) << 32;
            parsed_mac |= ((uint64_t)*((uint8_t*)&new_mac + 3)) << 24;
            parsed_mac |= ((uint64_t)*((uint8_t*)&new_mac + 2)) << 16;
            parsed_mac |= ((uint64_t)*((uint8_t*)&new_mac + 1)) << 8;
            parsed_mac |= ((uint64_t)*((uint8_t*)&new_mac));
            
            if (parsed_mac != reg.cached_mac) {
              reg.cached_mac = parsed_mac;
              reg.needs_update = true;
            }
          }
        }
      }
    }
  };
  
  update_registrations(this->registered_sensors_.temperature);
  update_registrations(this->registered_sensors_.humidity);
  update_registrations(this->registered_sensors_.movement_count);
  update_registrations(this->registered_sensors_.pitch);
  update_registrations(this->registered_sensors_.roll);
  update_registrations(this->registered_sensors_.battery_voltage);
  update_registrations(this->registered_sensors_.battery_level);
  update_registrations(this->registered_sensors_.rssi);
  update_registrations(this->registered_sensors_.movement_state);
  update_registrations(this->registered_sensors_.magnetic_detected);
  update_registrations(this->registered_sensors_.low_battery);
}

uint64_t TeltonikaBLEComponent::parse_mac_address(const std::string &mac_str) {
  uint8_t bytes[6];
  if (sscanf(mac_str.c_str(), "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
             &bytes[0], &bytes[1], &bytes[2], &bytes[3], &bytes[4], &bytes[5]) != 6) {
    return 0;
  }
  
  uint64_t mac = 0;
  for (int i = 0; i < 6; i++) {
    mac |= ((uint64_t)bytes[i]) << (8 * (5 - i));
  }
  return mac;
}

}  // namespace teltonika_ble
}  // namespace esphome