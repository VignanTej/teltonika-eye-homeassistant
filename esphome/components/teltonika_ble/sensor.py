import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    CONF_MAC_ADDRESS,
    CONF_TEMPERATURE,
    CONF_HUMIDITY,
    CONF_BATTERY_VOLTAGE,
    CONF_BATTERY_LEVEL,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_CELSIUS,
    UNIT_PERCENT,
    UNIT_VOLT,
    UNIT_EMPTY,
)

from . import teltonika_ble_ns, TeltonikaBLEComponent

DEPENDENCIES = ["teltonika_ble"]

CONF_TELTONIKA_BLE_ID = "teltonika_ble_id"
CONF_MOVEMENT_COUNT = "movement_count"
CONF_PITCH = "pitch"
CONF_ROLL = "roll"
CONF_RSSI = "rssi"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_TELTONIKA_BLE_ID): cv.use_id(TeltonikaBLEComponent),
        cv.Required(CONF_MAC_ADDRESS): cv.templatable(cv.mac_address),
        cv.Optional(CONF_TEMPERATURE): sensor.sensor_schema(
            unit_of_measurement=UNIT_CELSIUS,
            accuracy_decimals=2,
            device_class=DEVICE_CLASS_TEMPERATURE,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_HUMIDITY): sensor.sensor_schema(
            unit_of_measurement=UNIT_PERCENT,
            accuracy_decimals=0,
            device_class=DEVICE_CLASS_HUMIDITY,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_MOVEMENT_COUNT): sensor.sensor_schema(
            unit_of_measurement=UNIT_EMPTY,
            accuracy_decimals=0,
            state_class=STATE_CLASS_TOTAL_INCREASING,
        ),
        cv.Optional(CONF_PITCH): sensor.sensor_schema(
            unit_of_measurement="°",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_ROLL): sensor.sensor_schema(
            unit_of_measurement="°",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_BATTERY_VOLTAGE): sensor.sensor_schema(
            unit_of_measurement=UNIT_VOLT,
            accuracy_decimals=3,
            device_class=DEVICE_CLASS_VOLTAGE,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_BATTERY_LEVEL): sensor.sensor_schema(
            unit_of_measurement=UNIT_PERCENT,
            accuracy_decimals=0,
            device_class=DEVICE_CLASS_BATTERY,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_RSSI): sensor.sensor_schema(
            unit_of_measurement="dBm",
            accuracy_decimals=0,
            device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_TELTONIKA_BLE_ID])
    
    # Handle templatable MAC address
    mac_config = config[CONF_MAC_ADDRESS]
    
    if CONF_TEMPERATURE in config:
        sens = await sensor.new_sensor(config[CONF_TEMPERATURE])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_temperature_sensor(template_, sens))
    
    if CONF_HUMIDITY in config:
        sens = await sensor.new_sensor(config[CONF_HUMIDITY])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_humidity_sensor(template_, sens))
    
    if CONF_MOVEMENT_COUNT in config:
        sens = await sensor.new_sensor(config[CONF_MOVEMENT_COUNT])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_movement_count_sensor(template_, sens))
    
    if CONF_PITCH in config:
        sens = await sensor.new_sensor(config[CONF_PITCH])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_pitch_sensor(template_, sens))
    
    if CONF_ROLL in config:
        sens = await sensor.new_sensor(config[CONF_ROLL])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_roll_sensor(template_, sens))
    
    if CONF_BATTERY_VOLTAGE in config:
        sens = await sensor.new_sensor(config[CONF_BATTERY_VOLTAGE])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_battery_voltage_sensor(template_, sens))
    
    if CONF_BATTERY_LEVEL in config:
        sens = await sensor.new_sensor(config[CONF_BATTERY_LEVEL])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_battery_level_sensor(template_, sens))
    
    if CONF_RSSI in config:
        sens = await sensor.new_sensor(config[CONF_RSSI])
        template_ = await cg.templatable(mac_config, [], cg.std_string)
        cg.add(parent.register_rssi_sensor(template_, sens))