import logging
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
from homeassistant.components.climate.const import (
    HVACMode, HVACAction
)

_LOGGER = logging.getLogger(__name__)



class AprilaireTemperatureSensor(SensorEntity):
    """Sensor for the current temperature of a thermostat."""

    def __init__(self, interface, sn, name):
        """Initialize the temperature sensor."""
        self._interface = interface
        self._sn = sn
        self._attr_name = f"Aprilaire {name} Temperature"
        self._attr_device_class = "temperature"
        self._attr_native_unit_of_measurement = "°F"
        self._temperature = None

    @property
    def native_value(self):
        """Return the current temperature."""
        return self._temperature

    async def async_update(self):
        """Fetch the latest temperature."""
        try:
            temp = await self._interface.get_temperature(self._sn)
            if temp and temp > 10:
                self._temperature = temp
        except Exception as e:
            _LOGGER.error(f"Error updating temperature for thermostat {self._sn}: {e}")


class AprilaireModeSensor(SensorEntity):
    """Sensor for the current mode of a thermostat."""

    def __init__(self, interface, sn, name):
        """Initialize the mode sensor."""
        self._interface = interface
        self._sn = sn
        self._attr_name = f"Aprilaire {name} Mode"
        self._mode = None

    @property
    def native_value(self):
        """Return the current mode."""
        return self._mode

    async def async_update(self):
        """Fetch the latest mode."""
        try:
            mode = await self._interface.get_mode(self._sn)
            if mode in HVACMode:
                self._mode = mode
        except Exception as e:
            _LOGGER.error(f"Error updating mode for thermostat {self._sn}: {e}")



class AprilaireActionSensor(SensorEntity):
    """Action for the current mode of a thermostat."""

    def __init__(self, interface, sn, name):
        """Initialize the mode sensor."""
        self._interface = interface
        self._sn = sn
        self._attr_name = f"Aprilaire {name} Action"
        self._action = None

    @property
    def native_value(self):
        """Return the current mode."""
        return self._action

    async def async_update(self):
        """Fetch the latest mode."""
        try:
            action = await self._interface.get_state(self._sn)
            if action in HVACAction:
                self._action = action
        except Exception as e:
            _LOGGER.error(f"Error updating action for thermostat {self._sn}: {e}")