"""Parser for Teltonika EYE Sensors."""
from __future__ import annotations

import logging
import struct
from typing import Any

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)

from .const import (
    TELTONIKA_COMPANY_ID,
    PROTOCOL_VERSION,
    FLAG_TEMPERATURE,
    FLAG_HUMIDITY,
    FLAG_MAGNETIC_SENSOR,
    FLAG_MAGNETIC_STATE,
    FLAG_MOVEMENT_COUNTER,
    FLAG_MOVEMENT_ANGLE,
    FLAG_LOW_BATTERY,
    FLAG_BATTERY_VOLTAGE,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


class TeltonikaEYEParser:
    """Parser for Teltonika EYE sensor data."""

    def update(self, data: PassiveBluetoothDataUpdate) -> PassiveBluetoothDataUpdate:
        """Update from BLE advertisement data."""
        # Check if this is a Teltonika device
        if TELTONIKA_COMPANY_ID not in data.manufacturer_data:
            return data

        manufacturer_data = data.manufacturer_data[TELTONIKA_COMPANY_ID]
        
        if len(manufacturer_data) < 2:
            return data

        protocol_version = manufacturer_data[0]
        if protocol_version != PROTOCOL_VERSION:
            return data

        flags = manufacturer_data[1]
        
        # Parse sensor data
        parsed_data = self._parse_sensor_data(manufacturer_data, flags)
        
        # Create entity updates
        entity_data = {}
        entity_names = {}
        
        # Temperature sensor
        if "temperature" in parsed_data:
            key = PassiveBluetoothEntityKey("temperature", data.address)
            entity_data[key] = parsed_data["temperature"]["value"]
            entity_names[key] = "Temperature"

        # Humidity sensor
        if "humidity" in parsed_data:
            key = PassiveBluetoothEntityKey("humidity", data.address)
            entity_data[key] = parsed_data["humidity"]["value"]
            entity_names[key] = "Humidity"

        # Battery voltage sensor
        if "battery_voltage" in parsed_data:
            key = PassiveBluetoothEntityKey("battery_voltage", data.address)
            entity_data[key] = parsed_data["battery_voltage"]["value"]
            entity_names[key] = "Battery Voltage"

        # Movement count sensor
        if "movement" in parsed_data:
            key = PassiveBluetoothEntityKey("movement_count", data.address)
            entity_data[key] = parsed_data["movement"]["count"]
            entity_names[key] = "Movement Count"

        # Movement state binary sensor
        if "movement" in parsed_data:
            key = PassiveBluetoothEntityKey("movement_state", data.address)
            entity_data[key] = parsed_data["movement"]["state"] == "moving"
            entity_names[key] = "Movement State"

        # Magnetic field binary sensor (FIXED: corrected open/closed logic)
        if "magnetic" in parsed_data:
            key = PassiveBluetoothEntityKey("magnetic_field", data.address)
            entity_data[key] = parsed_data["magnetic"]["state"] == "closed"
            entity_names[key] = "Magnetic Field"

        # Low battery binary sensor
        key = PassiveBluetoothEntityKey("low_battery", data.address)
        entity_data[key] = parsed_data.get("battery", {}).get("low", False)
        entity_names[key] = "Low Battery"

        # Angle sensors
        if "angle" in parsed_data:
            pitch_key = PassiveBluetoothEntityKey("pitch", data.address)
            roll_key = PassiveBluetoothEntityKey("roll", data.address)
            entity_data[pitch_key] = parsed_data["angle"]["pitch"]
            entity_data[roll_key] = parsed_data["angle"]["roll"]
            entity_names[pitch_key] = "Pitch"
            entity_names[roll_key] = "Roll"

        # RSSI sensor
        rssi_key = PassiveBluetoothEntityKey("rssi", data.address)
        entity_data[rssi_key] = data.rssi
        entity_names[rssi_key] = "Signal Strength"

        # Update the data object
        data.entity_data = entity_data
        data.entity_names = entity_names
        
        # Set device info
        data.device_name = data.name or f"Teltonika EYE {data.address[-8:].replace(':', '')}"
        data.manufacturer = MANUFACTURER
        data.model = MODEL
        data.sw_version = str(protocol_version)

        return data

    def _parse_sensor_data(self, data: bytes, flags: int) -> dict[str, Any]:
        """Parse sensor data based on flags."""
        sensors = {}
        data_offset = 2

        # Parse temperature
        if flags & (1 << FLAG_TEMPERATURE):
            if data_offset + 2 <= len(data):
                temp_raw = struct.unpack('>H', data[data_offset:data_offset+2])[0]
                sensors["temperature"] = {
                    "value": temp_raw / 100.0,
                    "unit": "°C",
                    "raw": temp_raw
                }
                data_offset += 2

        # Parse humidity
        if flags & (1 << FLAG_HUMIDITY):
            if data_offset + 1 <= len(data):
                humidity = data[data_offset]
                sensors["humidity"] = {
                    "value": humidity,
                    "unit": "%",
                    "raw": humidity
                }
                data_offset += 1

        # Parse movement counter
        if flags & (1 << FLAG_MOVEMENT_COUNTER):
            if data_offset + 2 <= len(data):
                movement_raw = struct.unpack('>H', data[data_offset:data_offset+2])[0]
                movement_state = (movement_raw >> 15) & 1
                movement_count = movement_raw & 0x7FFF
                
                sensors["movement"] = {
                    "state": "moving" if movement_state else "stationary",
                    "count": movement_count,
                    "raw": movement_raw
                }
                data_offset += 2

        # Parse movement angle
        if flags & (1 << FLAG_MOVEMENT_ANGLE):
            if data_offset + 3 <= len(data):
                pitch_raw = struct.unpack('b', data[data_offset:data_offset+1])[0]
                roll_raw = struct.unpack('>h', data[data_offset+1:data_offset+3])[0]
                
                sensors["angle"] = {
                    "pitch": pitch_raw,
                    "roll": roll_raw,
                    "unit": "degrees"
                }
                data_offset += 3

        # Parse battery voltage
        if flags & (1 << FLAG_BATTERY_VOLTAGE):
            if data_offset + 1 <= len(data):
                voltage_raw = data[data_offset]
                voltage_mv = 2000 + (voltage_raw * 10)
                voltage_v = voltage_mv / 1000.0
                
                sensors["battery_voltage"] = {
                    "value": voltage_v,
                    "unit": "V",
                    "millivolts": voltage_mv,
                    "raw": voltage_raw
                }
                data_offset += 1

        # Parse magnetic sensor state (FIXED: corrected open/closed logic)
        if flags & (1 << FLAG_MAGNETIC_SENSOR):
            magnetic_detected = bool(flags & (1 << FLAG_MAGNETIC_STATE))
            sensors["magnetic"] = {
                "detected": magnetic_detected,
                "state": "closed" if magnetic_detected else "open"  # FIXED: Was reversed
            }

        # Parse battery status
        sensors["battery"] = {
            "low": bool(flags & (1 << FLAG_LOW_BATTERY))
        }

        return sensors