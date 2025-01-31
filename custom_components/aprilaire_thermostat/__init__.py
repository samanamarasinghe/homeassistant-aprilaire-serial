import logging

# Import necessary Home Assistant components
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT, CONF_BAUDRATE

# Define constants
DOMAIN = "aprilaire_thermostat"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Aprilaire thermostat integration from YAML."""
    _LOGGER.info("Setting up Aprilaire thermostat from YAML (if applicable)")
    # If you don't support YAML config, you can skip this function
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Aprilaire thermostat integration from a config entry."""
    _LOGGER.info("Setting up Aprilaire thermostat from config entry")

    # Get user-defined configuration values
    port = entry.data[CONF_PORT]
    baudrate = entry.data.get(CONF_BAUDRATE, 9600)

    # Initialize and manage the serial connection (example)
    try:
        from serial import Serial
        serial_connection = Serial(port, baudrate, timeout=1)

        # Test the connection with a simple command (e.g., SN? for all addresses)
        serial_connection.write(b"SN?\r")
        response = serial_connection.read(100).decode('utf-8')
        _LOGGER.info(f"Received response: {response}")
        
        # You might want to store the serial connection for further use
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["serial_connection"] = serial_connection

    except Exception as e:
        _LOGGER.error(f"Failed to set up serial connection: {e}")
        return False

    # Register platforms (e.g., climate) to create entities
    hass.config_entries.async_setup_platforms(entry, ["climate"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    _LOGGER.info("Unloading Aprilaire thermostat integration")

    # Close the serial connection, if open
    serial_connection = hass.data[DOMAIN].get("serial_connection")
    if serial_connection:
        serial_connection.close()

    # Unload platforms (e.g., climate)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate"])

    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok
