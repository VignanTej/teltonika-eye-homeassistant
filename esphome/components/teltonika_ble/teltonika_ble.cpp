#include "teltonika_ble.h"

namespace esphome {
namespace teltonika_ble {

static const char *const TAG = "teltonika_ble";

TeltonikaBLEComponent::TeltonikaBLEComponent() = default;

void TeltonikaBLEComponent::setup() {
  ESP_LOGI(TAG, "Setting up Teltonika BLE component...");
  ESP_LOGI(TAG, "Discover mode: %s", this->discover_ ? "enabled" : "disabled"); 
  this->last_scan_ms_ = millis();
  ESP_LOGI(TAG, "Teltonika BLE component setup complete");
}

void TeltonikaBLEComponent::loop() {
  uint32_t now = millis();
  this->apply_timeout_logic(now);
}

void TeltonikaBLEComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "Teltonika BLE:");
  ESP_LOGCONFIG(TAG, " Discover devices: %s", YESNO(this->discover_));
  ESP_LOGCONFIG(TAG, "  Global timeout: %u ms", this->global_timeout_ms_);
  ESP_LOGCONFIG(TAG, "  Registered sensor MACs: %d", this->registered_sensors_.temperature.size());
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
  bool has_sensors = (this->registered_sensors_.temperature.find(mac) != this->registered_sensors_.temperature.end() ||
                      this->registered_sensors_.humidity.find(mac) != this->registered_sensors_.humidity.end() ||
                      this->registered_sensors_.movement_count.find(mac) != this->registered_sensors_.movement_count.end() ||
                      this->registered_sensors_.pitch.find(mac) != this->registered_sensors_.pitch.end() ||
                      this->registered_sensors_.roll.find(mac) != this->registered_sensors_.roll.end() ||
                      this->registered_sensors_.battery_voltage.find(mac) != this->registered_sensors_.battery_voltage.end() ||
                      this->registered_sensors_.battery_level.find(mac) != this->registered_sensors_.battery_level.end() ||
                      this->registered_sensors_.rssi.find(mac) != this->registered_sensors_.rssi.end() ||
                      this->registered_sensors_.movement_state.find(mac) != this->registered_sensors_.movement_state.end() ||
                      this->registered_sensors_.magnetic_detected.find(mac) != this->registered_sensors_.magnetic_detected.end() ||
                      this->registered_sensors_.low_battery.find(mac) != this->registered_sensors_.low_battery.end());

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

  // Parse magnetic sensor
  cached.magnetic_detected = (flags & (1 << 3)) != 0;
  
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

  // Publish all sensor values if registered
  auto temp_it = this->registered_sensors_.temperature.find(mac);
  if (temp_it != this->registered_sensors_.temperature.end()) {
    publish(temp_it->second, values.temperature_c);
  }
  
  auto hum_it = this->registered_sensors_.humidity.find(mac);
  if (hum_it != this->registered_sensors_.humidity.end()) {
    publish(hum_it->second, values.humidity_percent);
  }
  
  auto mv_count_it = this->registered_sensors_.movement_count.find(mac);
  if (mv_count_it != this->registered_sensors_.movement_count.end()) {
    publish(mv_count_it->second, values.movement_count);
  }
  
  auto pitch_it = this->registered_sensors_.pitch.find(mac);
  if (pitch_it != this->registered_sensors_.pitch.end()) {
    publish(pitch_it->second, values.pitch_deg);
  }
  
  auto roll_it = this->registered_sensors_.roll.find(mac);
  if (roll_it != this->registered_sensors_.roll.end()) {
    publish(roll_it->second, values.roll_deg);
  }
  
  auto batt_v_it = this->registered_sensors_.battery_voltage.find(mac);
  if (batt_v_it != this->registered_sensors_.battery_voltage.end()) {
    publish(batt_v_it->second, values.battery_voltage_v);
  }
  
  auto batt_l_it = this->registered_sensors_.battery_level.find(mac);
  if (batt_l_it != this->registered_sensors_.battery_level.end()) {
    publish(batt_l_it->second, values.battery_level_percent);
  }
  
  auto rssi_it = this->registered_sensors_.rssi.find(mac);
  if (rssi_it != this->registered_sensors_.rssi.end()) {
    publish(rssi_it->second, values.rssi_dbm);
  }
  
  // Publish binary sensors  
  auto mv_state_it = this->registered_sensors_.movement_state.find(mac);
  if (mv_state_it != this->registered_sensors_.movement_state.end()) {
    publish_binary(mv_state_it->second, values.movement_state);
  }
  
  auto mag_it = this->registered_sensors_.magnetic_detected.find(mac);
  if (mag_it != this->registered_sensors_.magnetic_detected.end()) {
    publish_binary(mag_it->second, values.magnetic_detected);
  }
  
  auto low_batt_it = this->registered_sensors_.low_battery.find(mac);
  if (low_batt_it != this->registered_sensors_.low_battery.end()) {
    publish_binary(low_batt_it->second, values.low_battery);
  }

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
    
    // Publish NAN to all registered sensors for this device
    auto temp_it = this->registered_sensors_.temperature.find(mac);
    if (temp_it != this->registered_sensors_.temperature.end()) {
      temp_it->second->publish_state(NAN);
    }
    
    auto hum_it = this->registered_sensors_.humidity.find(mac);
    if (hum_it != this->registered_sensors_.humidity.end()) {
      hum_it->second->publish_state(NAN);
    }
    
    // Clear movement count, pitch, roll, battery sensors similarly
    auto mv_count_it = this->registered_sensors_.movement_count.find(mac);
    if (mv_count_it != this->registered_sensors_.movement_count.end()) {
      mv_count_it->second->publish_state(NAN);
    }
    
    auto pitch_it = this->registered_sensors_.pitch.find(mac);
    if (pitch_it != this->registered_sensors_.pitch.end()) {
      pitch_it->second->publish_state(NAN);
    }
    
    auto roll_it = this->registered_sensors_.roll.find(mac);
    if (roll_it != this->registered_sensors_.roll.end()) {
      roll_it->second->publish_state(NAN);
    }
    
    auto batt_v_it = this->registered_sensors_.battery_voltage.find(mac);
    if (batt_v_it != this->registered_sensors_.battery_voltage.end()) {
      batt_v_it->second->publish_state(NAN);
    }
    
    auto batt_l_it = this->registered_sensors_.battery_level.find(mac);
    if (batt_l_it != this->registered_sensors_.battery_level.end()) {
      batt_l_it->second->publish_state(NAN);
    }
    
    auto rssi_it = this->registered_sensors_.rssi.find(mac);
    if (rssi_it != this->registered_sensors_.rssi.end()) {
      rssi_it->second->publish_state(NAN);
    }
    
    // Set binary sensors to false
    auto mv_state_it = this->registered_sensors_.movement_state.find(mac);
    if (mv_state_it != this->registered_sensors_.movement_state.end()) {
      mv_state_it->second->publish_state(false);
    }
    
    auto mag_it = this->registered_sensors_.magnetic_detected.find(mac);
    if (mag_it != this->registered_sensors_.magnetic_detected.end()) {
      mag_it->second->publish_state(false);
    }
    
    auto low_batt_it = this->registered_sensors_.low_battery.find(mac);
    if (low_batt_it != this->registered_sensors_.low_battery.end()) {
      low_batt_it->second->publish_state(false);
    }
    
    this->device_timeouts_.erase(mac);
    this->cache_.erase(mac);
  }
}

}  // namespace teltonika_ble
}  // namespace esphome