import logging
from pymodbus.client import ModbusSerialClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_BAUDRATE, CONF_SLAVE_ID

_LOGGER = logging.getLogger(__name__)

# Define the platforms used in this integration
PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Veris Branch Power Monitor integration from YAML."""
    _LOGGER.info("Setting up Veris Branch Power Monitor from YAML (if applicable)")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Veris Branch Power Monitor from a config entry."""
    _LOGGER.info("Setting up Veris Branch Power Monitor from config entry")

    port = entry.data.get(CONF_PORT)
    baudrate = entry.data.get(CONF_BAUDRATE, 9600)
    slave_id = entry.data.get(CONF_SLAVE_ID, 2)  # Default slave ID 2

    try:
        # Initialize Modbus Serial Client
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity='N',  # No parity
            stopbits=1,
            bytesize=8,
            timeout=2
        )

        if not client.connect():
            _LOGGER.error("Failed to connect to Modbus device")
            raise ConfigEntryNotReady("Modbus connection failed")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["client"] = client
        hass.data[DOMAIN]["slave_id"] = slave_id

        _LOGGER.info("Modbus connection established successfully")

    except Exception as e:
        _LOGGER.error(f"Failed to set up Modbus connection: {e}")
        raise ConfigEntryNotReady from e

    # Forward platform setups (sensors)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    _LOGGER.info("Unloading Veris Branch Power Monitor integration")

    client = hass.data[DOMAIN].get("client")
    if client:
        client.close()  # Close the Modbus connection gracefully

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok
