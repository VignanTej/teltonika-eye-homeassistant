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
        cv.Required(CONF_MAC_ADDRESS): cv.templatable(cv.mac_address),
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
    
    # Handle templatable MAC address
    mac_config = config[CONF_MAC_ADDRESS]
    
    if CONF_MOVEMENT in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_MOVEMENT])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_movement_sensor(template_, sens))
    
    if CONF_MAGNETIC in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_MAGNETIC])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_magnetic_sensor(template_, sens))
    
    if CONF_LOW_BATTERY in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_LOW_BATTERY])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_low_battery_sensor(template_, sens))