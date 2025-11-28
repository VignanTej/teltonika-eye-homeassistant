import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import esp32_ble_tracker
from esphome.const import CONF_ID, CONF_MAC_ADDRESS, CONF_NAME, CONF_TIMEOUT
from esphome import automation

AUTO_LOAD = ["sensor", "binary_sensor"]

CONF_DISCOVER = "discover"
CONF_DEVICES = "devices"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_RSSI = "rssi"
CONF_BATTERY_LEVEL = "battery_level"

teltonika_ble_ns = cg.esphome_ns.namespace("teltonika_ble")
TeltonikaBLEComponent = teltonika_ble_ns.class_("TeltonikaBLEComponent", cg.Component, esp32_ble_tracker.ESPBTDeviceListener)

TeltonikaDeviceConfig = teltonika_ble_ns.struct_("TeltonikaDeviceConfig")

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(TeltonikaBLEComponent),
            cv.Optional(CONF_DISCOVER, default=False): cv.boolean,
            cv.Optional(CONF_SCAN_INTERVAL, default="60s"): cv.positive_time_period_seconds,
            cv.Optional(CONF_TIMEOUT, default="300s"): cv.positive_time_period_seconds,
            cv.Optional(CONF_RSSI, default=True): cv.boolean,
            cv.Optional(CONF_BATTERY_LEVEL, default=True): cv.boolean,
            cv.Optional(CONF_DEVICES, default=[]): cv.ensure_list(
                cv.Schema(
                    {
                        cv.Required(CONF_MAC_ADDRESS): cv.mac_address,
                        cv.Optional(CONF_NAME): cv.string,
                        cv.Optional(CONF_TIMEOUT): cv.positive_time_period_seconds,
                        cv.Optional(CONF_RSSI): cv.boolean,
                        cv.Optional(CONF_BATTERY_LEVEL): cv.boolean,
                    }
                )
            ),
        }
    )
    .extend(esp32_ble_tracker.ESP_BLE_DEVICE_SCHEMA)
)


async def to_code(config):
    component = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(component, config)
    await esp32_ble_tracker.register_ble_device(component, config)

    cg.add(component.set_discover(config[CONF_DISCOVER]))
    cg.add(component.set_global_scan_interval(config[CONF_SCAN_INTERVAL]))
    cg.add(component.set_global_timeout(config[CONF_TIMEOUT]))
    cg.add(component.set_global_rssi_enabled(config[CONF_RSSI]))
    cg.add(component.set_global_battery_level_enabled(config[CONF_BATTERY_LEVEL]))

    for device_conf in config[CONF_DEVICES]:
        await _register_device(component, device_conf)


async def _register_device(component, device_conf):
    # Convert MAC address to uint64_t
    # The MAC address is a cv.MacAddress object with parts attribute
    mac_address = device_conf[CONF_MAC_ADDRESS]
    # Build uint64 from MAC parts [AA, BB, CC, DD, EE, FF]
    mac_parts = mac_address.parts
    mac_value = 0
    for i, part in enumerate(mac_parts):
        mac_value |= (part << (8 * (5 - i)))
    
    mac_int = cg.RawExpression(f"0x{mac_value:012X}ULL")
    
    name = device_conf.get(CONF_NAME, "")
    timeout_ms = device_conf.get(CONF_TIMEOUT, 0)
    enable_rssi = device_conf.get(CONF_RSSI, True)
    enable_battery_level = device_conf.get(CONF_BATTERY_LEVEL, True)
    
    # Pass device configuration directly to the C++ component
    cg.add(component.add_device(mac_int, cg.std_string(name), timeout_ms, enable_rssi, enable_battery_level))