import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text_sensor
from esphome.const import (
    CONF_ID,
    ICON_BLUETOOTH,
)

from . import teltonika_ble_ns, TeltonikaBLEComponent

DEPENDENCIES = ["teltonika_ble"]

CONF_TELTONIKA_BLE_ID = "teltonika_ble_id"
CONF_DISCOVERED_DEVICES = "discovered_devices"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_TELTONIKA_BLE_ID): cv.use_id(TeltonikaBLEComponent),
        cv.Optional(CONF_DISCOVERED_DEVICES): text_sensor.text_sensor_schema(
            icon=ICON_BLUETOOTH,
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_TELTONIKA_BLE_ID])
    
    if CONF_DISCOVERED_DEVICES in config:
        sens = await text_sensor.new_text_sensor(config[CONF_DISCOVERED_DEVICES])
        cg.add(parent.set_discovered_devices_text_sensor(sens))