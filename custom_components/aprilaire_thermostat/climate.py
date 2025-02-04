from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE
)
from homeassistant.const import TEMP_FAHRENHEIT, ATTR_TEMPERATURE
import logging
from aprilair_serial_interface import AprilaireSerialInterface

_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup climate entities for Aprilaire thermostats."""
    interface = AprilaireSerialInterface()
    thermostats = interface.query_thermostats()

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
        self._target_temperature = None
        self._hvac_mode = HVAC_MODE_OFF
        self._preset_mode = None

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement for temperature."""
        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def supported_features(self):
        """Return the features supported by this thermostat."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return SUPPORTED_HVAC_MODES

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature for the thermostat."""
        if ATTR_TEMPERATURE in kwargs:
            target_temp = kwargs[ATTR_TEMPERATURE]
            _LOGGER.info("Setting target temperature to %s°F for %s", target_temp, self._sn)
            self._interface.set_setpoint(self._sn, "SETPOINTHEAT", target_temp)
            self._target_temperature = target_temp
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode for the thermostat."""
        if hvac_mode not in SUPPORTED_HVAC_MODES:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return

        _LOGGER.info("Setting HVAC mode to %s for %s", hvac_mode, self._sn)
        # Implement HVAC mode command here (e.g., send HVAC_MODE= command)
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new data from the Aprilaire thermostat."""
        _LOGGER.debug("Updating Aprilaire thermostat %s", self._sn)

        # Get current temperature
        self._current_temperature = self._interface.get_temperature(self._sn)

        # Get target temperature (e.g., setpoint)
        # Here, you could implement separate commands for reading setpoints if needed

        # Get HVAC mode if available
        # For now, simulate it as heating if temperature is below a threshold
        if self._current_temperature is not None and self._target_temperature is not None:
            if self._current_temperature < self._target_temperature:
                self._hvac_mode = HVAC_MODE_HEAT
            else:
                self._hvac_mode = HVAC_MODE_OFF
