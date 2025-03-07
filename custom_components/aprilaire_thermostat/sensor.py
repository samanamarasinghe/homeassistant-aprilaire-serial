import logging
import asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from homeassistant.components.climate.const import (
    HVACMode, HVACAction
)


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.error(f"Setting up ")
    """Set up Aprilaire sensors based on a config entry."""
    thermostat_data = None
    while not thermostat_data:
        thermostat_data = hass.data["aprilaire_thermostat"].get("thermostats")
        if not thermostat_data:
            await asyncio.sleep(5)

    if not thermostat_data:
        _LOGGER.error("No thermostat data found in hass.data! Check integration setup.")
        return
        
    interface, thermostats, names = thermostat_data
    sensors = [
        AprilaireTemperatureSensor(interface, sn, name)
        for sn, name in zip(thermostats, names)
    ] + [
        AprilaireModeSensor(interface, sn, name)
        for sn, name in zip(thermostats, names)
    ] + [
        AprilaireActionSensor(interface, sn, name)
        for sn, name in zip(thermostats, names)
    ] + [
        AprilaireSetpointSensor(interface, sn, name)
        for sn, name in zip(thermostats, names)
    ] + [
        AprilaireConnectionSensor(interface, name)  # Add connection sensor
        for name in names
    ]

    async_add_entities(sensors, update_before_add=True)


class AprilaireConnectionSensor(SensorEntity):
    """A sensor to monitor the connection status of the Aprilaire thermostat."""

    def __init__(self, interface, name):
        """Initialize the sensor."""
        self._interface = interface
        self._attr_name = f"{name} Connection Status"
        self._attr_unique_id = f"aprilaire_{name}_connection"
        self._attr_device_class = "connectivity"  # Optional for sensors
        self._attr_native_unit_of_measurement = None  # No unit
        self._connection_status = "Disconnected"

    @property
    def native_value(self):
        """Return the connection status as a string (instead of binary True/False)."""
        return self._connection_status

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            connected = await self._interface.check_connection()
            self._connection_status = "Connected" if connected else "Disconnected"
        except Exception as e:
            _LOGGER.error(f"Error updating connection status: {e}")
            self._connection_status = "Error"

class AprilaireTemperatureSensor(SensorEntity):
    """Sensor for the current temperature of a thermostat."""

    def __init__(self, interface, sn, name):
        """Initialize the temperature sensor."""
        self._interface = interface
        self._sn = sn
        self._attr_name = f"Aprilaire {name} Temperature"
        self._attr_unique_id = f"aprilaire_{sn}_{name}_temprature"
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
        self._attr_unique_id = f"aprilaire_{sn}_{name}_mode"
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
        self._attr_unique_id = f"aprilaire_{sn}_{name}_action"        
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


class AprilaireSetpointSensor(SensorEntity):
    """Sensor for the current setpoint of a thermostat."""

    def __init__(self, interface, sn, name):
        """Initialize the setpoint sensor."""
        self._interface = interface
        self._sn = sn
        self._attr_name = f"Aprilaire {name} Setpoint"
        self._attr_unique_id = f"aprilaire_{sn}_{name}_setpoint"
        self._attr_device_class = "temperature"
        self._attr_native_unit_of_measurement = "°F"
        self._temperature = None

    @property
    def native_value(self):
        """Return the setpoint temperature."""
        return self._temperature

    async def async_update(self):
        """Fetch the setpoint temperature."""
        try:
            mode = await self._interface.get_mode(self._sn)
            if mode in [HVACMode.HEAT, HVACMode.COOL]:
                temp = await self._interface.get_setpoint(self._sn, mode)
                # Sometimes the temprature reading can get bad values. If so, keep the old!
                if 50 <= temp <= 90:
                    self._temperature = temp
            else:
                self._temperature = None
            
        except Exception as e:
            _LOGGER.error(f"Error getting the setpoint for thermostat {self._sn}: {e}")
