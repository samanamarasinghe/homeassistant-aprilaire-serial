import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, CONF_BAUDRATE
from .aprilair_serial_interface import AprilaireThermostatSerialInterface

_LOGGER = logging.getLogger(__name__)

# Pre-import platform modules to avoid blocking during async setup
PLATFORMS = ["climate"]

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
        # Initialize and connect the interface asynchronously
        interface = AprilaireThermostatSerialInterface(port, baudrate)
        await interface.connect()  # Asynchronous connection

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["interface"] = interface

        _LOGGER.info("Serial connection established successfully")

    except Exception as e:
        _LOGGER.error(f"Failed to set up serial connection: {e}")
        raise ConfigEntryNotReady from e

    # Use the updated method to forward platform setups
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    _LOGGER.info("Unloading Aprilaire thermostat integration")

    interface = hass.data[DOMAIN].get("interface")
    if interface:
        interface.close()  # Close the serial connection gracefully

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok
