import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import esp32_ble_tracker
from esphome.const import CONF_ID, CONF_TIMEOUT

AUTO_LOAD = ["sensor", "binary_sensor"]

CONF_DISCOVER = "discover"

teltonika_ble_ns = cg.esphome_ns.namespace("teltonika_ble")
TeltonikaBLEComponent = teltonika_ble_ns.class_(
    "TeltonikaBLEComponent", cg.Component, esp32_ble_tracker.ESPBTDeviceListener
)

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(TeltonikaBLEComponent),
            cv.Optional(CONF_DISCOVER, default=True): cv.boolean,
            cv.Optional(CONF_TIMEOUT, default="300s"): cv.positive_time_period_seconds,
        }
    ).extend(esp32_ble_tracker.ESP_BLE_DEVICE_SCHEMA)
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await esp32_ble_tracker.register_ble_device(var, config)

    cg.add(var.set_discover(config[CONF_DISCOVER]))
    cg.add(var.set_global_timeout(config[CONF_TIMEOUT]))