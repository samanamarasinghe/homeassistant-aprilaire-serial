from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.util.unit_system import UnitOfTemperature
import logging
from .aprilair_serial_interface import AprilaireThermostatSerialInterface
from .const import ATTR_TEMPERATURE


_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup climate entities for Aprilaire thermostats."""
    interface = AprilaireThermostatSerialInterface()
    thermostats = await interface.query_thermostats()

    if not thermostats:
        _LOGGER.error("No thermostats found")
        interface.close()
        return

    entities = [AprilaireThermostat(interface, sn) for sn in thermostats]
    async_add_entities(entities)
    _LOGGER.info("Aprilaire climate entities added successfully.")

class AprilaireThermostat(ClimateEntity):
    """Representation of an Aprilaire thermostat."""

    def __init__(self, interface, sn):
        """Initialize the thermostat entity."""
        self._interface = interface
        self._sn = sn
        self._name = f"Aprilaire Thermostat {sn}"
        self._current_temperature = None
        self._setpoint_cool_temperature = None
        self._setpoint_heat_temperature = None
        self._hvac_mode = HVACMode.OFF
        self._preset_mode = None

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement for temperature."""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self): 
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if self._hvac_mode == HVACMode.COOL:
            return self._setpoint_cool_temperature
        elif self._hvac_mode == HVACMode.HEAT:
            return self._setpoint_heat_temperature
        else:
            return None

    @property
    def hvac_mode(self): 
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def supported_features(self):
        """Return the features supported by this thermostat."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return SUPPORTED_HVAC_MODES

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature for the thermostat."""
        if ATTR_TEMPERATURE in kwargs:
            target_temp = kwargs[ATTR_TEMPERATURE]
            _LOGGER.info("Setting target temperature to %s°F for %s", target_temp, self._sn)
            await self._interface.set_setpoint(self._sn, "SETPOINTHEAT", target_temp)
            self._target_temperature = target_temp
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, mode):
        """Set the HVAC mode for the thermostat."""
        if mode not in SUPPORTED_HVAC_MODES:
            _LOGGER.error("Unsupported HVAC mode: %s", mode)
            return

        await self._interface.set_mode(self._sn, mode)
        self._hvac_mode = mode
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new data from the Aprilaire thermostat."""
        _LOGGER.debug("Updating Aprilaire thermostat %s", self._sn)

        # Get current temperature
        tt = await self._interface.get_temperature(self._sn)
        if tt:
            self._current_temperature = tt 

        # Get target temperature (e.g., setpoint)
        # Here, you could implement separate commands for reading setpoints if needed
        sht = await self._interface.get_setpoint(self._sn, HVACMode.HEAT)
        sct = await self._interface.get_setpoint(self._sn, HVACMode.COOL)

        if sht:
            self._setpoint_heat_temperature = sht
        if sct:
            self._setpoint_cool_temperature = sct

        # Get HVAC mode if available
        md = await self._interface.get_mode(self._sn)
        if md:
            self._hvac_mode = md

