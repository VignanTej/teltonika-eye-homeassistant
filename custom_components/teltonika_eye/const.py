"""Constants for the Teltonika EYE Sensors integration."""

DOMAIN = "teltonika_eye"

# Teltonika Company ID
TELTONIKA_COMPANY_ID = 0x089A

# Protocol constants
PROTOCOL_VERSION = 0x01

# Flag bit positions
FLAG_TEMPERATURE = 0
FLAG_HUMIDITY = 1
FLAG_MAGNETIC_SENSOR = 2
FLAG_MAGNETIC_STATE = 3
FLAG_MOVEMENT_COUNTER = 4
FLAG_MOVEMENT_ANGLE = 5
FLAG_LOW_BATTERY = 6
FLAG_BATTERY_VOLTAGE = 7

# Default configuration
DEFAULT_SCAN_DURATION = 5.0
DEFAULT_SCAN_INTERVAL = 30

# Device information
MANUFACTURER = "Teltonika"
MODEL = "EYE Sensor"

# Entity names
CONF_SCAN_DURATION = "scan_duration"