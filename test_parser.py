#!/usr/bin/env python3
"""
Test script for Teltonika EYE sensor parser using sample data from documentation.
"""

import json
from teltonika_eye_scanner import TeltonikaEYEParser


def test_sample_data():
    """Test parser with sample data from Teltonika documentation."""
    
    # Sample data from documentation (manufacturer-specific part only)
    # Original hex: 9A0801B708B4120CCB0BFFC767
    # Breaking it down:
    # 9A08 - Teltonika company ID (little endian, so 0x089A)
    # 01 - Protocol version
    # B7 - Flags (0xB7 = 10110111 binary)
    # 08B4 - Temperature (2228 decimal = 22.28°C)
    # 12 - Humidity (18%)
    # 0CCB - Movement (3275 count, not moving)
    # 0BFFC7 - Angle (pitch: 11°, roll: -57°)
    # 67 - Battery voltage (103 -> 2000 + 103*10 = 3030mV)
    
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


def test_minimal_data():
    """Test parser with minimal data (only flags, no sensor values)."""
    print("\n" + "="*50)
    print("Testing minimal data (flags only)")
    print("="*50)
    
    # Only protocol version and flags, no sensor data
    minimal_data = {
        0x089A: bytes.fromhex("0100")  # Protocol version 1, flags 0x00 (no sensors)
    }
    
    parser = TeltonikaEYEParser()
    result = parser.parse_manufacturer_data(minimal_data)
    
    if result:
        print("✅ Minimal data test successful!")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Minimal data test failed")


def test_invalid_data():
    """Test parser with invalid data."""
    print("\n" + "="*50)
    print("Testing invalid data")
    print("="*50)
    
    parser = TeltonikaEYEParser()
    
    # Test with non-Teltonika company ID
    invalid_company = {
        0x004C: bytes.fromhex("01B708B4120CCB0BFFC767")  # Apple company ID
    }
    result = parser.parse_manufacturer_data(invalid_company)
    print(f"Non-Teltonika device: {'✅ Correctly ignored' if result is None else '❌ Should be ignored'}")
    
    # Test with insufficient data
    insufficient_data = {
        0x089A: bytes.fromhex("01")  # Only protocol version, no flags
    }
    result = parser.parse_manufacturer_data(insufficient_data)
    print(f"Insufficient data: {'✅ Correctly handled' if result is None else '❌ Should be rejected'}")
    
    # Test with wrong protocol version
    wrong_version = {
        0x089A: bytes.fromhex("02B708B4120CCB0BFFC767")  # Protocol version 2
    }
    result = parser.parse_manufacturer_data(wrong_version)
    print(f"Wrong protocol version: {'✅ Correctly handled' if result is None else '❌ Should be rejected'}")


if __name__ == "__main__":
    print("🧪 Testing Teltonika EYE Sensor Parser")
    print("="*50)
    
    test_sample_data()
    test_minimal_data()
    test_invalid_data()
    
    print("\n🎉 All tests completed!")