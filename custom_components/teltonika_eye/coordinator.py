"""Data update coordinator for Teltonika EYE Sensors with Bluetooth proxy support."""
from __future__ import annotations

import logging
import struct
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_track_bluetooth_advertisement,
)
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
    """Class to manage Teltonika EYE sensors via Home Assistant Bluetooth integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        approved_devices: set[str] | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.discovered_devices: Dict[str, Dict[str, Any]] = {}
        self.approved_devices = approved_devices or set()
        self.ignored_devices: set[str] = set()
        self._bluetooth_cancel = None

    async def async_start(self) -> None:
        """Start listening for Bluetooth advertisements via HA Bluetooth integration."""
        self.logger.debug("Starting Bluetooth advertisement tracking")
        
        # Track advertisements for Teltonika devices
        self._bluetooth_cancel = async_track_bluetooth_advertisement(
            self.hass,
            self._bluetooth_callback,
            {"manufacturer_id": TELTONIKA_COMPANY_ID},
        )
        
        # Also check for already discovered devices
        await self._check_existing_discoveries()

    async def async_stop(self) -> None:
        """Stop listening for Bluetooth advertisements."""
        if self._bluetooth_cancel:
            self._bluetooth_cancel()
            self._bluetooth_cancel = None

    async def _check_existing_discoveries(self) -> None:
        """Check for already discovered Teltonika devices."""
        discovered = async_discovered_service_info(self.hass)
        
        for service_info in discovered:
            if TELTONIKA_COMPANY_ID in service_info.manufacturer_data:
                self._process_advertisement(service_info)

    @callback
    def _bluetooth_callback(
        self, service_info: BluetoothServiceInfoBleak, change: str
    ) -> None:
        """Handle Bluetooth advertisement callback."""
        if change == "advertisement":
            self._process_advertisement(service_info)

    def _process_advertisement(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Process a Bluetooth advertisement."""
        parsed_data = self._parse_manufacturer_data(service_info)
        if not parsed_data:
            return

        device_address = service_info.address
        
        # Check if device is ignored
        if device_address in self.ignored_devices:
            return

        # Store discovered device
        self.discovered_devices[device_address] = parsed_data

        # If device is approved, add to active devices
        if device_address in self.approved_devices:
            self.devices[device_address] = parsed_data
            self.async_set_updated_data(self.devices)
        else:
            # Send notification for new device discovery
            self._send_discovery_notification(parsed_data)

    def _send_discovery_notification(self, device_data: Dict[str, Any]) -> None:
        """Send notification about discovered device."""
        device_name = device_data["device"]["name"]
        device_address = device_data["device"]["address"]
        
        # Only send notification if we haven't already notified about this device
        notification_id = f"teltonika_eye_discovery_{device_address.replace(':', '')}"
        
        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "New Teltonika EYE Sensor Discovered",
                    "message": f"Found sensor '{device_name}' ({device_address}). "
                              f"Temperature: {device_data['data']['sensors'].get('temperature', {}).get('value', 'N/A')}°C, "
                              f"Humidity: {device_data['data']['sensors'].get('humidity', {}).get('value', 'N/A')}%. "
                              f"Go to Settings → Devices & Services → Teltonika EYE Sensors "
                              f"to add or ignore this device.",
                    "notification_id": notification_id,
                },
            )
        )

    async def _async_update_data(self) -> Dict[str, Dict[str, Any]]:
        """Update data via Bluetooth integration."""
        # With Bluetooth integration, data is updated via callbacks
        # This method mainly serves to keep the coordinator active
        return self.devices

    def approve_device(self, device_address: str) -> None:
        """Approve a discovered device for monitoring."""
        if device_address in self.discovered_devices:
            self.approved_devices.add(device_address)
            self.devices[device_address] = self.discovered_devices[device_address]
            
            # Dismiss discovery notification
            notification_id = f"teltonika_eye_discovery_{device_address.replace(':', '')}"
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": notification_id},
                )
            )
            
            self.async_set_updated_data(self.devices)
            self.logger.info(f"Approved device {device_address} for monitoring")

    def ignore_device(self, device_address: str) -> None:
        """Ignore a discovered device."""
        self.ignored_devices.add(device_address)
        self.discovered_devices.pop(device_address, None)
        
        # Dismiss discovery notification
        notification_id = f"teltonika_eye_discovery_{device_address.replace(':', '')}"
        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": notification_id},
            )
        )
        
        self.logger.info(f"Ignored device {device_address}")

    def _parse_manufacturer_data(
        self, service_info: BluetoothServiceInfoBleak
    ) -> Optional[Dict[str, Any]]:
        """Parse Teltonika manufacturer-specific data."""
        if TELTONIKA_COMPANY_ID not in service_info.manufacturer_data:
            return None

        data = service_info.manufacturer_data[TELTONIKA_COMPANY_ID]
        
        if len(data) < 2:
            return None

        protocol_version = data[0]
        if protocol_version != PROTOCOL_VERSION:
            return None

        flags = data[1]
        
        # Initialize result
        result = {
            "device": {
                "address": service_info.address,
                "name": service_info.name or f"Teltonika EYE {service_info.address[-8:].replace(':', '')}",
                "rssi": service_info.rssi,
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
        """Parse magnetic sensor state if present (FIXED: corrected open/closed logic)."""
        if flags & (1 << FLAG_MAGNETIC_SENSOR):
            # FIXED: Reversed the logic - magnetic field detected = closed, not detected = open
            magnetic_detected = bool(flags & (1 << FLAG_MAGNETIC_STATE))
            result["data"]["sensors"]["magnetic"] = {
                "detected": magnetic_detected,
                "state": "closed" if magnetic_detected else "open"  # FIXED: Was reversed
            }