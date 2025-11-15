"""Support for Teltonika EYE sensor entities."""
from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika EYE sensor entities."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    processor = PassiveBluetoothDataProcessor(
        lambda service_info, last_service_info: TeltonikaEYESensorProcessor(
            coordinator, service_info.address
        )
    )
    
    coordinator.async_register_processor(processor)


class TeltonikaEYESensorProcessor:
    """Processor for Teltonika EYE sensor data."""

    def __init__(self, coordinator: PassiveBluetoothProcessorCoordinator, address: str) -> None:
        """Initialize the processor."""
        self.coordinator = coordinator
        self.address = address

    def process(self, service_info, last_service_info) -> list[PassiveBluetoothProcessorEntity]:
        """Process the service info and return entities."""
        entities = []
        
        # Temperature sensor
        entities.append(
            TeltonikaEYETemperatureSensor(
                self.coordinator,
                self.address,
                "temperature",
            )
        )
        
        # Humidity sensor
        entities.append(
            TeltonikaEYEHumiditySensor(
                self.coordinator,
                self.address,
                "humidity",
            )
        )
        
        # Battery voltage sensor
        entities.append(
            TeltonikaEYEBatteryVoltageSensor(
                self.coordinator,
                self.address,
                "battery_voltage",
            )
        )
        
        # Movement count sensor
        entities.append(
            TeltonikaEYEMovementCountSensor(
                self.coordinator,
                self.address,
                "movement_count",
            )
        )
        
        # Pitch sensor
        entities.append(
            TeltonikaEYEPitchSensor(
                self.coordinator,
                self.address,
                "pitch",
            )
        )
        
        # Roll sensor
        entities.append(
            TeltonikaEYERollSensor(
                self.coordinator,
                self.address,
                "roll",
            )
        )
        
        # RSSI sensor
        entities.append(
            TeltonikaEYERSSISensor(
                self.coordinator,
                self.address,
                "rssi",
            )
        )
        
        return entities


class TeltonikaEYESensorBase(PassiveBluetoothProcessorEntity, SensorEntity):
    """Base class for Teltonika EYE sensors."""

    def __init__(
        self,
        coordinator: PassiveBluetoothProcessorCoordinator,
        address: str,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, address, key)


class TeltonikaEYETemperatureSensor(TeltonikaEYESensorBase):
    """Temperature sensor for Teltonika EYE."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS


class TeltonikaEYEHumiditySensor(TeltonikaEYESensorBase):
    """Humidity sensor for Teltonika EYE."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE


class TeltonikaEYEBatteryVoltageSensor(TeltonikaEYESensorBase):
    """Battery voltage sensor for Teltonika EYE."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT


class TeltonikaEYEMovementCountSensor(TeltonikaEYESensorBase):
    """Movement count sensor for Teltonika EYE."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:motion-sensor"


class TeltonikaEYEPitchSensor(TeltonikaEYESensorBase):
    """Pitch angle sensor for Teltonika EYE."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:angle-acute"


class TeltonikaEYERollSensor(TeltonikaEYESensorBase):
    """Roll angle sensor for Teltonika EYE."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:angle-acute"


class TeltonikaEYERSSISensor(TeltonikaEYESensorBase):
    """RSSI sensor for Teltonika EYE."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_category = "diagnostic"