import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Aprilaire binary sensors based on a config entry."""
    interface = hass.data[DOMAIN]["interface"]

    sensors = [
        AprilaireConnectionSensor(interface, "aprilaire_connection")
    ]

    async_add_entities(sensors, update_before_add=True)


class AprilaireConnectionSensor(BinarySensorEntity):
    """A binary sensor to monitor the connection status of the Aprilaire thermostat."""

    def __init__(self, interface, name):
        """Initialize the binary sensor."""
        self._interface = interface
        self._attr_name = name
        self._attr_device_class = "connectivity"
        self._is_connected = False

    @property
    def is_on(self):
        """Return true if the sensor is on (connected)."""
        return self._is_connected

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            self._is_connected = await self._interface.check_connection()
        except Exception as e:
            _LOGGER.error(f"Error updating connection status: {e}")
            self._is_connected = False