#!/usr/bin/env python3
"""
Teltonika EYE Sensor Bluetooth LE Scanner

This script scans for Teltonika EYE sensors via Bluetooth LE and parses their
advertising data to extract sensor readings (temperature, humidity, movement, etc.).
Outputs structured JSON data to stdout for integration with IoT systems.

Based on Teltonika EYE Sensor BLE Protocol Documentation.
"""

import asyncio
import json
import logging
import struct
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


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


class TeltonikaEYEScanner:
    """Bluetooth LE scanner for Teltonika EYE sensors."""
    
    def __init__(self, scan_duration: float = 10.0, output_format: str = "json"):
        self.scan_duration = scan_duration
        self.output_format = output_format
        self.parser = TeltonikaEYEParser()
        self.logger = logging.getLogger(__name__)
        self.devices_found = {}
    
    async def scan_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """Callback function called for each discovered BLE device."""
        try:
            # Parse manufacturer data
            if advertisement_data.manufacturer_data:
                parsed_data = self.parser.parse_manufacturer_data(advertisement_data.manufacturer_data)
                
                if parsed_data:
                    # Add device information
                    device_info = {
                        "device": {
                            "address": device.address,
                            "name": device.name or "Unknown",
                            "rssi": advertisement_data.rssi
                        },
                        "data": parsed_data
                    }
                    
                    # Store/update device data
                    self.devices_found[device.address] = device_info
                    
                    # Output immediately for real-time processing
                    if self.output_format == "json":
                        print(json.dumps(device_info, indent=None))
                        sys.stdout.flush()
                    
                    self.logger.info(f"Found Teltonika EYE sensor: {device.address} ({device.name})")
        
        except Exception as e:
            self.logger.error(f"Error processing device {device.address}: {e}")
    
    async def scan(self) -> List[Dict[str, Any]]:
        """
        Scan for Teltonika EYE sensors.
        
        Returns:
            List of discovered sensor data
        """
        self.logger.info(f"Starting BLE scan for {self.scan_duration} seconds...")
        
        try:
            scanner = BleakScanner(detection_callback=self.scan_callback)
            await scanner.start()
            await asyncio.sleep(self.scan_duration)
            await scanner.stop()
            
            self.logger.info(f"Scan completed. Found {len(self.devices_found)} Teltonika EYE sensors.")
            
            return list(self.devices_found.values())
        
        except Exception as e:
            self.logger.error(f"Error during BLE scan: {e}")
            return []


async def main():
    """Main function to run the scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scan for Teltonika EYE sensors and output sensor data as JSON"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=10.0,
        help="Scan duration in seconds (default: 10.0)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr  # Log to stderr to keep stdout clean for JSON output
    )
    
    # Create and run scanner
    scanner = TeltonikaEYEScanner(scan_duration=args.duration)
    
    try:
        await scanner.scan()
    except KeyboardInterrupt:
        logging.info("Scan interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())