import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_BAUDRATE

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Aprilaire thermostat integration from YAML."""
    _LOGGER.info("Setting up Aprilaire thermostat from YAML (if applicable)")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Aprilaire thermostat integration from a config entry."""
    _LOGGER.info("Setting up Aprilaire thermostat from config entry")

    port = entry.data[CONF_PORT]
    baudrate = entry.data.get(CONF_BAUDRATE, 9600)

    try:
        # Run blocking code in executor to avoid blocking the event loop
        serial_connection = await hass.async_add_executor_job(setup_serial_connection, port, baudrate)
        if not serial_connection:
            raise ConfigEntryNotReady("Unable to establish serial connection")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["serial_connection"] = serial_connection

    except Exception as e:
        _LOGGER.error(f"Failed to set up serial connection: {e}")
        raise ConfigEntryNotReady from e

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    _LOGGER.info("Unloading Aprilaire thermostat integration")

    serial_connection = hass.data[DOMAIN].get("serial_connection")
    if serial_connection:
        serial_connection.close()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate"])

    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok

def setup_serial_connection(port, baudrate):
    """Set up the serial connection (blocking)."""
    from serial import Serial
    try:
        serial_connection = Serial(port, baudrate, timeout=1)
        serial_connection.write(b"SN?\r")
        response = serial_connection.read(100).decode('utf-8')
        return serial_connection
    except Exception as e:
        _LOGGER.error(f"Error setting up serial connection: {e}")
        return None
