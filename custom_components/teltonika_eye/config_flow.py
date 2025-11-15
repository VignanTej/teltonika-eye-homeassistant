"""Config flow for Teltonika EYE Sensors integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_SCAN_DURATION, CONF_SCAN_DURATION, TELTONIKA_COMPANY_ID
from .coordinator import TeltonikaEYECoordinator

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_DURATION, default=DEFAULT_SCAN_DURATION): vol.All(
            vol.Coerce(float), vol.Range(min=1.0, max=30.0)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Check if Bluetooth integration is available
    if "bluetooth" not in hass.config.components:
        raise CannotConnect("Bluetooth integration not found. Please set up Bluetooth integration first.")

    # Check for discovered Teltonika devices
    discovered = async_discovered_service_info(hass)
    teltonika_devices = [
        service_info for service_info in discovered
        if TELTONIKA_COMPANY_ID in service_info.manufacturer_data
    ]
    
    if not teltonika_devices:
        _LOGGER.warning("No Teltonika EYE sensors found during validation")

    return {"title": "Teltonika EYE Sensors"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Teltonika EYE Sensors."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.discovered_devices: dict[str, dict[str, Any]] = {}
        self.selected_devices: set[str] = set()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Discover available devices
                await self._discover_devices()
                
                if self.discovered_devices:
                    # Show device selection step
                    return await self.async_step_select_devices()
                else:
                    # No devices found, but still allow setup for future discovery
                    return self.async_create_entry(
                        title=info["title"], 
                        data={"approved_devices": []}
                    )
                    
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _discover_devices(self) -> None:
        """Discover Teltonika EYE devices."""
        discovered = async_discovered_service_info(self.hass)
        
        # Create temporary coordinator for parsing
        temp_coordinator = TeltonikaEYECoordinator(
            self.hass, _LOGGER, "temp", timedelta(seconds=30)
        )
        
        for service_info in discovered:
            if TELTONIKA_COMPANY_ID in service_info.manufacturer_data:
                parsed_data = temp_coordinator._parse_manufacturer_data(service_info)
                if parsed_data:
                    self.discovered_devices[service_info.address] = parsed_data

    async def async_step_select_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection step."""
        if user_input is not None:
            selected_devices = user_input.get("devices", [])
            
            return self.async_create_entry(
                title="Teltonika EYE Sensors",
                data={"approved_devices": selected_devices}
            )

        # Create device selection schema
        device_options = {}
        for address, device_data in self.discovered_devices.items():
            device_name = device_data["device"]["name"]
            sensors = device_data["data"]["sensors"]
            
            # Create descriptive label
            sensor_info = []
            if "temperature" in sensors:
                sensor_info.append(f"Temp: {sensors['temperature']['value']}°C")
            if "humidity" in sensors:
                sensor_info.append(f"Humidity: {sensors['humidity']['value']}%")
            if "battery_voltage" in sensors:
                sensor_info.append(f"Battery: {sensors['battery_voltage']['value']}V")
            
            label = f"{device_name} ({address})"
            if sensor_info:
                label += f" - {', '.join(sensor_info)}"
            
            device_options[address] = label

        if not device_options:
            # No devices found, proceed with empty setup
            return self.async_create_entry(
                title="Teltonika EYE Sensors",
                data={"approved_devices": []}
            )

        schema = vol.Schema({
            vol.Optional("devices", default=[]): vol.All(
                vol.Ensure(list),
                [vol.In(device_options)]
            )
        })

        return self.async_show_form(
            step_id="select_devices",
            data_schema=schema,
            description_placeholders={
                "device_count": str(len(device_options))
            }
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Teltonika EYE Sensors."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Handle device management
            if "manage_devices" in user_input:
                return await self.async_step_manage_devices()
            
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_DURATION,
                        default=self.config_entry.options.get(
                            CONF_SCAN_DURATION, DEFAULT_SCAN_DURATION
                        ),
                    ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=30.0)),
                    vol.Optional("manage_devices", default=False): bool,
                }
            ),
        )

    async def async_step_manage_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage approved and discovered devices."""
        coordinator: TeltonikaEYECoordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
        
        if user_input is not None:
            # Update approved devices
            new_approved = set(user_input.get("approved_devices", []))
            new_ignored = set(user_input.get("ignored_devices", []))
            
            # Update coordinator
            for device_address in new_approved:
                if device_address not in coordinator.approved_devices:
                    coordinator.approve_device(device_address)
            
            for device_address in new_ignored:
                coordinator.ignore_device(device_address)
            
            # Update config entry
            new_data = dict(self.config_entry.data)
            new_data["approved_devices"] = list(new_approved)
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            
            return self.async_create_entry(title="", data={})

        # Create device management schema
        all_devices = {**coordinator.devices, **coordinator.discovered_devices}
        
        approved_options = {}
        discovered_options = {}
        
        for address, device_data in all_devices.items():
            device_name = device_data["device"]["name"]
            sensors = device_data["data"]["sensors"]
            
            # Create descriptive label
            sensor_info = []
            if "temperature" in sensors:
                sensor_info.append(f"Temp: {sensors['temperature']['value']}°C")
            if "humidity" in sensors:
                sensor_info.append(f"Humidity: {sensors['humidity']['value']}%")
            
            label = f"{device_name} ({address})"
            if sensor_info:
                label += f" - {', '.join(sensor_info)}"
            
            if address in coordinator.approved_devices:
                approved_options[address] = label
            else:
                discovered_options[address] = label

        schema_dict = {}
        
        if approved_options:
            schema_dict[vol.Optional("approved_devices", default=list(approved_options.keys()))] = vol.All(
                vol.Ensure(list),
                [vol.In(approved_options)]
            )
        
        if discovered_options:
            schema_dict[vol.Optional("ignored_devices", default=[])] = vol.All(
                vol.Ensure(list),
                [vol.In(discovered_options)]
            )

        if not schema_dict:
            return self.async_abort(reason="no_devices")

        return self.async_show_form(
            step_id="manage_devices",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "approved_count": str(len(approved_options)),
                "discovered_count": str(len(discovered_options)),
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""