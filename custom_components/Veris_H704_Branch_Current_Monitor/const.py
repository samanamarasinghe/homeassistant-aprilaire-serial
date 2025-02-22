"""Constants for the Veris Branch Power Monitor integration."""

DOMAIN = "veris_branch_power_monitor"

# Configuration Keys
CONF_PORT = "port"
CONF_BAUDRATE = "baudrate"
CONF_SLAVE_ID = "slave_id"

# Default Values
DEFAULT_PORT = None  # Let the user specify this
DEFAULT_BAUDRATE = 9600
DEFAULT_SLAVE_ID = 2

# Sensor Configuration
REGISTER_COUNT = 42  # Number of registers to read per slave
SCAN_INTERVAL = 30  # Time in seconds between polling updates

# Logging
_LOGGER_NAME = "homeassistant.components.veris_branch_power_monitor"

