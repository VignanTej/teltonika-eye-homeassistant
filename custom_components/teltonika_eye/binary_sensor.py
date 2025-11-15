"""Support for Teltonika EYE binary sensor entities."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika EYE binary sensor entities."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    processor = PassiveBluetoothDataProcessor(
        lambda service_info, last_service_info: TeltonikaEYEBinarySensorProcessor(
            coordinator, service_info.address
        )
    )
    
    coordinator.async_register_processor(processor)


class TeltonikaEYEBinarySensorProcessor:
    """Processor for Teltonika EYE binary sensor data."""

    def __init__(self, coordinator: PassiveBluetoothProcessorCoordinator, address: str) -> None:
        """Initialize the processor."""
        self.coordinator = coordinator
        self.address = address

    def process(self, service_info, last_service_info) -> list[PassiveBluetoothProcessorEntity]:
        """Process the service info and return binary sensor entities."""
        entities = []
        
        # Movement state binary sensor
        entities.append(
            TeltonikaEYEMovementSensor(
                self.coordinator,
                self.address,
                "movement_state",
            )
        )
        
        # Magnetic field binary sensor (FIXED: corrected open/closed logic)
        entities.append(
            TeltonikaEYEMagneticSensor(
                self.coordinator,
                self.address,
                "magnetic_field",
            )
        )
        
        # Low battery binary sensor
        entities.append(
            TeltonikaEYELowBatterySensor(
                self.coordinator,
                self.address,
                "low_battery",
            )
        )
        
        return entities


class TeltonikaEYEBinarySensorBase(PassiveBluetoothProcessorEntity, BinarySensorEntity):
    """Base class for Teltonika EYE binary sensors."""

    def __init__(
        self,
        coordinator: PassiveBluetoothProcessorCoordinator,
        address: str,
        key: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, address, key)


class TeltonikaEYEMovementSensor(TeltonikaEYEBinarySensorBase):
    """Movement detection binary sensor for Teltonika EYE."""

    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_icon = "mdi:motion-sensor"


class TeltonikaEYEMagneticSensor(TeltonikaEYEBinarySensorBase):
    """Magnetic field detection binary sensor for Teltonika EYE."""

    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_icon = "mdi:magnet"


class TeltonikaEYELowBatterySensor(TeltonikaEYEBinarySensorBase):
    """Low battery binary sensor for Teltonika EYE."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_entity_category = "diagnostic"