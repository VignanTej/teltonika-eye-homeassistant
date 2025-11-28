import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from esphome.const import (
    CONF_ID,
    CONF_MAC_ADDRESS,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_BATTERY,
)

from . import teltonika_ble_ns, TeltonikaBLEComponent

DEPENDENCIES = ["teltonika_ble"]

CONF_TELTONIKA_BLE_ID = "teltonika_ble_id"
CONF_MOVEMENT = "movement"
CONF_MAGNETIC = "magnetic"
CONF_LOW_BATTERY = "low_battery"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_TELTONIKA_BLE_ID): cv.use_id(TeltonikaBLEComponent),
        cv.Required(CONF_MAC_ADDRESS): cv.mac_address,
        cv.Optional(CONF_MOVEMENT): binary_sensor.binary_sensor_schema(
            device_class=DEVICE_CLASS_MOTION
        ),
        cv.Optional(CONF_MAGNETIC): binary_sensor.binary_sensor_schema(
            device_class=DEVICE_CLASS_OPENING
        ),
        cv.Optional(CONF_LOW_BATTERY): binary_sensor.binary_sensor_schema(
            device_class=DEVICE_CLASS_BATTERY
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_TELTONIKA_BLE_ID])
    mac = config[CONF_MAC_ADDRESS]
    
    # Convert MAC to uint64 for C++
    mac_parts = mac.parts
    mac_value = 0
    for i, part in enumerate(mac_parts):
        mac_value |= (part << (8 * (5 - i)))
    mac_int = cg.RawExpression(f"0x{mac_value:012X}ULL")
    
    if CONF_MOVEMENT in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_MOVEMENT])
        cg.add(parent.register_movement_sensor(mac_int, sens))
    
    if CONF_MAGNETIC in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_MAGNETIC])
        cg.add(parent.register_magnetic_sensor(mac_int, sens))
    
    if CONF_LOW_BATTERY in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_LOW_BATTERY])
        cg.add(parent.register_low_battery_sensor(mac_int, sens))