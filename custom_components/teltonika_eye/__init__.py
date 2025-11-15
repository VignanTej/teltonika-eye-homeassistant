"""The Teltonika EYE Sensors integration."""
from __future__ import annotations

import logging

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .parser import TeltonikaEYEParser

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


def process_service_info(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: PassiveBluetoothDataUpdate,
) -> PassiveBluetoothDataUpdate:
    """Process service info."""
    return TeltonikaEYEParser().update(data)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Teltonika EYE Sensors from a config entry."""
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=None,  # Listen to all devices
        mode=BluetoothScanningMode.PASSIVE,
        update_method=process_service_info,
        entry=entry,
    )
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(
        coordinator.async_start()
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok