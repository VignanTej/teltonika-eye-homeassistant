#!/usr/bin/env python3
"""
Standalone test script for Teltonika EYE sensor parser that doesn't require bleak.
This extracts just the parser class for testing purposes.
"""

import json
import struct
import logging
from datetime import datetime
from typing import Dict, Optional, Any


class TeltonikaEYEParser:
    """Parser for Teltonika EYE sensor BLE advertising data."""
    
    # Teltonika Company ID (little endian in advertising data)
    TELTONIKA_COMPANY_ID = 0x089A
    PROTOCOL_VERSION = 0x01
    
    # Flag bit positions
    FLAG_TEMPERATURE = 0
    FLAG_HUMIDITY = 1
    FLAG_MAGNETIC_SENSOR = 2
    FLAG_MAGNETIC_STATE = 3
    FLAG_MOVEMENT_COUNTER = 4
    FLAG_MOVEMENT_ANGLE = 5
    FLAG_LOW_BATTERY = 6
    FLAG_BATTERY_VOLTAGE = 7
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_manufacturer_data(self, manufacturer_data: Dict[int, bytes]) -> Optional[Dict[str, Any]]:
        """
        Parse Teltonika manufacturer-specific data from BLE advertising packet.
        
        Args:
            manufacturer_data: Dictionary mapping company ID to manufacturer data bytes
            
        Returns:
            Parsed sensor data dictionary or None if not a Teltonika device
        """
        # Check if this is a Teltonika device
        if self.TELTONIKA_COMPANY_ID not in manufacturer_data:
            return None
        
        data = manufacturer_data[self.TELTONIKA_COMPANY_ID]
        
        if len(data) < 2:
            self.logger.warning("Insufficient manufacturer data length")
            return None
        
        # Parse protocol version and flags
        protocol_version = data[0]
        if protocol_version != self.PROTOCOL_VERSION:
            self.logger.warning(f"Unsupported protocol version: {protocol_version}")
            return None
        
        flags = data[1]
        self.logger.debug(f"Flags byte: 0x{flags:02X} (binary: {flags:08b})")
        
        # Initialize result dictionary
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "protocol_version": protocol_version,
            "flags": flags,
            "sensors": {}
        }
        
        # Parse sensor data based on flags
        data_offset = 2
        data_offset = self._parse_temperature(data, data_offset, flags, result)
        data_offset = self._parse_humidity(data, data_offset, flags, result)
        data_offset = self._parse_movement_counter(data, data_offset, flags, result)
        data_offset = self._parse_movement_angle(data, data_offset, flags, result)
        data_offset = self._parse_battery_voltage(data, data_offset, flags, result)
        
        # Parse magnetic sensor state
        self._parse_magnetic_sensor(flags, result)
        
        # Parse battery status
        self._parse_battery_status(flags, result)
        
        return result
    
    def _parse_temperature(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse temperature data if present."""
        if flags & (1 << self.FLAG_TEMPERATURE):
            if offset + 2 <= len(data):
                temp_raw = struct.unpack('>H', data[offset:offset+2])[0]  # Big-endian
                temperature_celsius = temp_raw / 100.0
                result["sensors"]["temperature"] = {
                    "value": temperature_celsius,
                    "unit": "°C",
                    "raw": temp_raw
                }
                self.logger.debug(f"Temperature: {temperature_celsius}°C (raw: {temp_raw})")
                return offset + 2
            else:
                self.logger.warning("Temperature flag set but insufficient data")
        return offset
    
    def _parse_humidity(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse humidity data if present."""
        if flags & (1 << self.FLAG_HUMIDITY):
            if offset + 1 <= len(data):
                humidity = data[offset]
                result["sensors"]["humidity"] = {
                    "value": humidity,
                    "unit": "%",
                    "raw": humidity
                }
                self.logger.debug(f"Humidity: {humidity}%")
                return offset + 1
            else:
                self.logger.warning("Humidity flag set but insufficient data")
        return offset
    
    def _parse_movement_counter(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse movement counter data if present."""
        if flags & (1 << self.FLAG_MOVEMENT_COUNTER):
            if offset + 2 <= len(data):
                movement_raw = struct.unpack('>H', data[offset:offset+2])[0]  # Big-endian
                movement_state = (movement_raw >> 15) & 1  # MSB
                movement_count = movement_raw & 0x7FFF     # 15 LSBs
                
                result["sensors"]["movement"] = {
                    "state": "moving" if movement_state else "stationary",
                    "count": movement_count,
                    "raw": movement_raw
                }
                self.logger.debug(f"Movement: {result['sensors']['movement']['state']}, count: {movement_count}")
                return offset + 2
            else:
                self.logger.warning("Movement counter flag set but insufficient data")
        return offset
    
    def _parse_movement_angle(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse movement angle data if present."""
        if flags & (1 << self.FLAG_MOVEMENT_ANGLE):
            if offset + 3 <= len(data):
                pitch_raw = struct.unpack('b', data[offset:offset+1])[0]  # signed byte
                roll_raw = struct.unpack('>h', data[offset+1:offset+3])[0]  # signed short, big-endian
                
                result["sensors"]["angle"] = {
                    "pitch": pitch_raw,
                    "roll": roll_raw,
                    "unit": "degrees"
                }
                self.logger.debug(f"Angle - Pitch: {pitch_raw}°, Roll: {roll_raw}°")
                return offset + 3
            else:
                self.logger.warning("Movement angle flag set but insufficient data")
        return offset
    
    def _parse_battery_voltage(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse battery voltage data if present."""
        if flags & (1 << self.FLAG_BATTERY_VOLTAGE):
            if offset + 1 <= len(data):
                voltage_raw = data[offset]
                voltage_mv = 2000 + (voltage_raw * 10)
                voltage_v = voltage_mv / 1000.0
                
                result["sensors"]["battery_voltage"] = {
                    "value": voltage_v,
                    "unit": "V",
                    "millivolts": voltage_mv,
                    "raw": voltage_raw
                }
                self.logger.debug(f"Battery voltage: {voltage_v}V ({voltage_mv}mV)")
                return offset + 1
            else:
                self.logger.warning("Battery voltage flag set but insufficient data")
        return offset
    
    def _parse_magnetic_sensor(self, flags: int, result: Dict[str, Any]) -> None:
        """Parse magnetic sensor state if present."""
        if flags & (1 << self.FLAG_MAGNETIC_SENSOR):
            magnetic_detected = bool(flags & (1 << self.FLAG_MAGNETIC_STATE))
            result["sensors"]["magnetic"] = {
                "detected": magnetic_detected,
                "state": "detected" if magnetic_detected else "not_detected"
            }
            self.logger.debug(f"Magnetic field: {result['sensors']['magnetic']['state']}")
    
    def _parse_battery_status(self, flags: int, result: Dict[str, Any]) -> None:
        """Parse battery status from flags."""
        low_battery = bool(flags & (1 << self.FLAG_LOW_BATTERY))
        result["battery"] = {
            "low": low_battery,
            "status": "low" if low_battery else "normal"
        }
        if low_battery:
            self.logger.debug("Low battery detected")


def test_sample_data():
    """Test parser with sample data from Teltonika documentation."""
    
    print("🧪 Testing Teltonika EYE Sensor Parser")
    print("="*50)
    
    # Sample data from documentation example
    # From the parsed example in documentation:
    # Protocol version: 01
    # Flags: B7 (10110111 binary)
    # Temperature: 08B4 (2228 decimal = 22.28°C)
    # Humidity: 12 (18 decimal = 18%)
    # Movement: 0CCB (3275 decimal, MSB=0 so stationary, count=3275)
    # Angle: 0BFFC7 (pitch=0B=11°, roll=FFC7=-57°)
    # Battery: 67 (103 decimal = 3030mV)
    
    sample_manufacturer_data = {
        0x089A: bytes.fromhex("01B708B4120CCB0BFFC767")
    }
    
    parser = TeltonikaEYEParser()
    result = parser.parse_manufacturer_data(sample_manufacturer_data)
    
    if result:
        print("✅ Parser test successful!")
        print(json.dumps(result, indent=2))
        
        # Validate expected values
        expected_values = {
            "temperature": 22.28,
            "humidity": 18,
            "movement_count": 3275,
            "movement_state": "stationary",
            "pitch": 11,
            "roll": -57,
            "battery_voltage": 3.030
        }
        
        sensors = result.get("sensors", {})
        
        print("\n🔍 Validation Results:")
        
        # Check temperature
        if "temperature" in sensors:
            temp_value = sensors["temperature"]["value"]
            if abs(temp_value - expected_values["temperature"]) < 0.01:
                print(f"✅ Temperature: {temp_value}°C (expected: {expected_values['temperature']}°C)")
            else:
                print(f"❌ Temperature: {temp_value}°C (expected: {expected_values['temperature']}°C)")
        
        # Check humidity
        if "humidity" in sensors:
            humidity_value = sensors["humidity"]["value"]
            if humidity_value == expected_values["humidity"]:
                print(f"✅ Humidity: {humidity_value}% (expected: {expected_values['humidity']}%)")
            else:
                print(f"❌ Humidity: {humidity_value}% (expected: {expected_values['humidity']}%)")
        
        # Check movement
        if "movement" in sensors:
            movement = sensors["movement"]
            if (movement["count"] == expected_values["movement_count"] and 
                movement["state"] == expected_values["movement_state"]):
                print(f"✅ Movement: {movement['state']}, count: {movement['count']}")
            else:
                print(f"❌ Movement: {movement['state']}, count: {movement['count']}")
        
        # Check angle
        if "angle" in sensors:
            angle = sensors["angle"]
            if (angle["pitch"] == expected_values["pitch"] and 
                angle["roll"] == expected_values["roll"]):
                print(f"✅ Angle: pitch {angle['pitch']}°, roll {angle['roll']}°")
            else:
                print(f"❌ Angle: pitch {angle['pitch']}°, roll {angle['roll']}°")
        
        # Check battery voltage
        if "battery_voltage" in sensors:
            voltage = sensors["battery_voltage"]["value"]
            if abs(voltage - expected_values["battery_voltage"]) < 0.001:
                print(f"✅ Battery voltage: {voltage}V (expected: {expected_values['battery_voltage']}V)")
            else:
                print(f"❌ Battery voltage: {voltage}V (expected: {expected_values['battery_voltage']}V)")
        
        # Check flags interpretation
        flags = result.get("flags", 0)
        print(f"\n📊 Flags analysis (0x{flags:02X} = {flags:08b}):")
        flag_names = [
            "Temperature", "Humidity", "Magnetic sensor", "Magnetic state",
            "Movement counter", "Movement angle", "Low battery", "Battery voltage"
        ]
        
        for i, name in enumerate(flag_names):
            bit_set = bool(flags & (1 << i))
            print(f"  Bit {i} ({name}): {'✅' if bit_set else '❌'}")
    
    else:
        print("❌ Parser test failed - no data returned")


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    
    test_sample_data()
    
    print("\n🎉 Test completed!")