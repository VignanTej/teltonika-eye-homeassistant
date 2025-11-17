"""Data update coordinator for Teltonika EYE Sensors."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
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
)


class TeltonikaEYECoordinator(DataUpdateCoordinator):
    """Class to manage Teltonika EYE sensors via BLE scanning."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        scan_duration: float = 5.0,
    ) -> None:
        """Initialize."""
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self.scan_duration = scan_duration
        self.devices: Dict[str, Dict[str, Any]] = {}

    async def _async_update_data(self) -> Dict[str, Dict[str, Any]]:
        """Update data via library."""
        try:
            return await self._scan_for_devices()
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception

    async def _scan_for_devices(self) -> Dict[str, Dict[str, Any]]:
        """Scan for Teltonika EYE devices."""
        discovered_devices = {}
        
        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            """Handle discovered device."""
            if advertisement_data.manufacturer_data:
                parsed_data = self._parse_manufacturer_data(
                    device, advertisement_data.manufacturer_data, advertisement_data.rssi
                )
                if parsed_data:
                    discovered_devices[device.address] = parsed_data

        try:
            scanner = BleakScanner(detection_callback=detection_callback)
            await scanner.start()
            await asyncio.sleep(self.scan_duration)
            await scanner.stop()
            
            # Update our devices dict with new data
            for address, data in discovered_devices.items():
                self.devices[address] = data
                
            return self.devices
            
        except Exception as err:
            self.logger.error("Error during BLE scan: %s", err)
            raise UpdateFailed(f"Error during BLE scan: {err}") from err

    def _parse_manufacturer_data(
        self, device: BLEDevice, manufacturer_data: Dict[int, bytes], rssi: int
    ) -> Optional[Dict[str, Any]]:
        """Parse Teltonika manufacturer-specific data."""
        if TELTONIKA_COMPANY_ID not in manufacturer_data:
            return None

        data = manufacturer_data[TELTONIKA_COMPANY_ID]
        
        if len(data) < 2:
            return None

        protocol_version = data[0]
        if protocol_version != PROTOCOL_VERSION:
            return None

        flags = data[1]
        
        # Initialize result
        result = {
            "device": {
                "address": device.address,
                "name": device.name or f"Teltonika EYE {device.address[-8:].replace(':', '')}",
                "rssi": rssi,
            },
            "data": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "protocol_version": protocol_version,
                "flags": flags,
                "sensors": {},
                "battery": {"low": bool(flags & (1 << FLAG_LOW_BATTERY))},
            }
        }

        # Parse sensor data based on flags
        data_offset = 2
        data_offset = self._parse_temperature(data, data_offset, flags, result)
        data_offset = self._parse_humidity(data, data_offset, flags, result)
        data_offset = self._parse_movement_counter(data, data_offset, flags, result)
        data_offset = self._parse_movement_angle(data, data_offset, flags, result)
        data_offset = self._parse_battery_voltage(data, data_offset, flags, result)
        
        # Parse magnetic sensor state (FIXED: corrected open/closed logic)
        self._parse_magnetic_sensor(flags, result)

        return result

    def _parse_temperature(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse temperature data if present."""
        if flags & (1 << FLAG_TEMPERATURE):
            if offset + 2 <= len(data):
                temp_raw = struct.unpack('>H', data[offset:offset+2])[0]
                temperature_celsius = temp_raw / 100.0
                result["data"]["sensors"]["temperature"] = {
                    "value": temperature_celsius,
                    "unit": "°C",
                    "raw": temp_raw
                }
                return offset + 2
        return offset

    def _parse_humidity(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse humidity data if present."""
        if flags & (1 << FLAG_HUMIDITY):
            if offset + 1 <= len(data):
                humidity = data[offset]
                result["data"]["sensors"]["humidity"] = {
                    "value": humidity,
                    "unit": "%",
                    "raw": humidity
                }
                return offset + 1
        return offset

    def _parse_movement_counter(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse movement counter data if present."""
        if flags & (1 << FLAG_MOVEMENT_COUNTER):
            if offset + 2 <= len(data):
                movement_raw = struct.unpack('>H', data[offset:offset+2])[0]
                movement_state = (movement_raw >> 15) & 1
                movement_count = movement_raw & 0x7FFF
                
                result["data"]["sensors"]["movement"] = {
                    "state": "moving" if movement_state else "stationary",
                    "count": movement_count,
                    "raw": movement_raw
                }
                return offset + 2
        return offset

    def _parse_movement_angle(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse movement angle data if present."""
        if flags & (1 << FLAG_MOVEMENT_ANGLE):
            if offset + 3 <= len(data):
                pitch_raw = struct.unpack('b', data[offset:offset+1])[0]
                roll_raw = struct.unpack('>h', data[offset+1:offset+3])[0]
                
                result["data"]["sensors"]["angle"] = {
                    "pitch": pitch_raw,
                    "roll": roll_raw,
                    "unit": "degrees"
                }
                return offset + 3
        return offset

    def _parse_battery_voltage(self, data: bytes, offset: int, flags: int, result: Dict[str, Any]) -> int:
        """Parse battery voltage data if present."""
        if flags & (1 << FLAG_BATTERY_VOLTAGE):
            if offset + 1 <= len(data):
                voltage_raw = data[offset]
                voltage_mv = 2000 + (voltage_raw * 10)
                voltage_v = voltage_mv / 1000.0
                
                result["data"]["sensors"]["battery_voltage"] = {
                    "value": voltage_v,
                    "unit": "V",
                    "millivolts": voltage_mv,
                    "raw": voltage_raw
                }
                return offset + 1
        return offset

    def _parse_magnetic_sensor(self, flags: int, result: Dict[str, Any]) -> None:
        """Parse magnetic sensor state if present.
        
        Maps physical sensor state to logical door/window state:
        - Magnetic field detected = door/window closed
        - No magnetic field = door/window open
        """
        if flags & (1 << FLAG_MAGNETIC_SENSOR):
            # Check if magnetic field is detected
            magnetic_detected = bool(flags & (1 << FLAG_MAGNETIC_STATE))
            result["data"]["sensors"]["magnetic"] = {
                "detected": magnetic_detected,
                "state": "closed" if magnetic_detected else "open"  # Physical state mapping
            }