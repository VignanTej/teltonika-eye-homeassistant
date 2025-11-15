"""Support for Teltonika EYE sensor entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TeltonikaEYECoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika EYE sensor entities."""
    coordinator: TeltonikaEYECoordinator = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_add_sensor_entities():
        """Add sensor entities for discovered devices."""
        entities = []
        
        for device_address, device_data in coordinator.data.items():
            sensors = device_data["data"]["sensors"]
            
            # Temperature sensor
            if "temperature" in sensors:
                entities.append(
                    TeltonikaEYETemperatureSensor(coordinator, device_address)
                )
            
            # Humidity sensor
            if "humidity" in sensors:
                entities.append(
                    TeltonikaEYEHumiditySensor(coordinator, device_address)
                )
            
            # Battery voltage sensor
            if "battery_voltage" in sensors:
                entities.append(
                    TeltonikaEYEBatteryVoltageSensor(coordinator, device_address)
                )
            
            # Movement count sensor
            if "movement" in sensors:
                entities.append(
                    TeltonikaEYEMovementCountSensor(coordinator, device_address)
                )
            
            # Angle sensors
            if "angle" in sensors:
                entities.append(
                    TeltonikaEYEPitchSensor(coordinator, device_address)
                )
                entities.append(
                    TeltonikaEYERollSensor(coordinator, device_address)
                )
            
            # RSSI sensor (always present)
            entities.append(
                TeltonikaEYERSSISensor(coordinator, device_address)
            )

        if entities:
            async_add_entities(entities)

    # Add entities for currently discovered devices
    async_add_sensor_entities()
    
    # Listen for new devices
    coordinator.async_add_listener(async_add_sensor_entities)


class TeltonikaEYESensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Teltonika EYE sensors."""

    def __init__(
        self,
        coordinator: TeltonikaEYECoordinator,
        device_address: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_address = device_address
        self.sensor_type = sensor_type
        
        device_data = coordinator.data.get(device_address, {})
        device_info = device_data.get("device", {})
        device_name = device_info.get("name", f"Teltonika EYE {device_address[-8:].replace(':', '')}")
        
        self._attr_unique_id = f"{device_address}_{sensor_type}"
        self._attr_name = f"{device_name} {sensor_type.replace('_', ' ').title()}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_address)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=str(device_data.get("data", {}).get("protocol_version", 1)),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.device_address in self.coordinator.data
        )


class TeltonikaEYETemperatureSensor(TeltonikaEYESensorBase):
    """Temperature sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device_address, "temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "temperature" in sensors:
            return sensors["temperature"]["value"]
        return None


class TeltonikaEYEHumiditySensor(TeltonikaEYESensorBase):
    """Humidity sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, device_address, "humidity")
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "humidity" in sensors:
            return sensors["humidity"]["value"]
        return None


class TeltonikaEYEBatteryVoltageSensor(TeltonikaEYESensorBase):
    """Battery voltage sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the battery voltage sensor."""
        super().__init__(coordinator, device_address, "battery_voltage")
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "battery_voltage" in sensors:
            return sensors["battery_voltage"]["value"]
        return None


class TeltonikaEYEMovementCountSensor(TeltonikaEYESensorBase):
    """Movement count sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the movement count sensor."""
        super().__init__(coordinator, device_address, "movement_count")
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:motion-sensor"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "movement" in sensors:
            return sensors["movement"]["count"]
        return None


class TeltonikaEYEPitchSensor(TeltonikaEYESensorBase):
    """Pitch angle sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the pitch sensor."""
        super().__init__(coordinator, device_address, "pitch")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "°"
        self._attr_icon = "mdi:angle-acute"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "angle" in sensors:
            return sensors["angle"]["pitch"]
        return None


class TeltonikaEYERollSensor(TeltonikaEYESensorBase):
    """Roll angle sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the roll sensor."""
        super().__init__(coordinator, device_address, "roll")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "°"
        self._attr_icon = "mdi:angle-acute"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        sensors = self.coordinator.data[self.device_address]["data"]["sensors"]
        if "angle" in sensors:
            return sensors["angle"]["roll"]
        return None


class TeltonikaEYERSSISensor(TeltonikaEYESensorBase):
    """RSSI sensor for Teltonika EYE."""

    def __init__(self, coordinator: TeltonikaEYECoordinator, device_address: str) -> None:
        """Initialize the RSSI sensor."""
        super().__init__(coordinator, device_address, "rssi")
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_entity_category = "diagnostic"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.device_address not in self.coordinator.data:
            return None
        
        device_data = self.coordinator.data[self.device_address]["device"]
        return device_data.get("rssi")