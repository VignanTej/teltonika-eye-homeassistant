"""Support for Teltonika EYE binary sensor entities."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TeltonikaEYECoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika EYE binary sensor entities."""
    coordinator: TeltonikaEYECoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    for device_address, device_data in coordinator.data.items():
        sensors = device_data["data"]["sensors"]
        
        # Movement state binary sensor
        if "movement" in sensors:
            entities.append(
                TeltonikaEYEMovementSensor(coordinator, device_address)
            )
        
        # Magnetic field binary sensor
        if "magnetic" in sensors:
            entities.append(
                TeltonikaEYEMagneticSensor(coordinator, device_address)
            )
        
        # Low battery binary sensor (always present)
        entities.append(
            TeltonikaEYELowBatterySensor(coordinator, device_address)
        )

    async_add_entities(entities)


class TeltonikaEYEBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Base class for Teltonika EYE binary sensors."""

    def __init__(
        self,
        coordinator: TeltonikaEYECoordinator,
        device_address: str,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device_address = device_address
        self.sensor_type = sensor_type
        
        device_data = coordinator.data[device_address]
        device_name = device_data["device"]["name"]
        
        self._attr_unique_id = f"{device_address}_{sensor_type}"
        self._attr_name = f"{device_name} {sensor_type.replace('_', ' ').title()}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_address)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=str(device_data["data"]["protocol_version"]),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.device_address in self.coordinator.data
        )


class TeltonikaEYEMovementSensor(TeltonikaEYEBinarySensorBase):
    """Movement detection binary sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the movement sensor."""
        super().__init__(coordinator, device_address, "movement_state")
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._attr_icon = "mdi:motion-sensor"

    @property
    def is_on(self) -> bool | None:
        """Return true if movement is detected."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "movement" in sensors:
            return sensors["movement"]["state"] == "moving"
        return None


class TeltonikaEYEMagneticSensor(TeltonikaEYEBinarySensorBase):
    """Magnetic field detection binary sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the magnetic sensor."""
        super().__init__(coordinator, device_address, "magnetic_field")
        self._attr_device_class = BinarySensorDeviceClass.OPENING
        self._attr_icon = "mdi:magnet"

    @property
    def is_on(self) -> bool | None:
        """Return true if magnetic field is detected."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "magnetic" in sensors:
            return sensors["magnetic"]["detected"]
        return None


class TeltonikaEYELowBatterySensor(TeltonikaEYEBinarySensorBase):
    """Low battery binary sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the low battery sensor."""
        super().__init__(coordinator, device_address, "low_battery")
        self._attr_device_class = BinarySensorDeviceClass.BATTERY
        self._attr_entity_category = "diagnostic"

    @property
    def is_on(self) -> bool | None:
        """Return true if battery is low."""
        if self.device_address not in self.coordinator.data:
            return None
        
        battery_data = self.coordinator.data[self.device_address]["data"]["battery"]
        return battery_data.get("low", False)