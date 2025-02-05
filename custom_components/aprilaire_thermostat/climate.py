from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.util.unit_system import UnitOfTemperature
import logging
import time
import random
from .aprilair_serial_interface import AprilaireThermostatSerialInterface
from .const import ATTR_TEMPERATURE
from homeassistant.util import Throttle
from datetime import timedelta

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup climate entities for Aprilaire thermostats."""
    port = config_entry.data.get("port", "/dev/ttyUSB0")
    baudrate = config_entry.data.get("baudrate", 9600)
    interface = AprilaireThermostatSerialInterface(port, baudrate)
    (thermostats, names) = await interface.query_thermostats()

    if not thermostats:
        _LOGGER.error("No thermostats found")
        interface.close()
        return
    
    _LOGGER.error(f"Using {port}:{baudrate} setting up Thermostats:{thermostats}, with names: {names}")

    entities = [AprilaireThermostat(interface, sn, nm, config_entry) for sn, nm in zip(thermostats, names)]
    async_add_entities(entities)

    _LOGGER.info("Aprilaire climate entities added successfully.")

class AprilaireThermostat(ClimateEntity):
    """Representation of an Aprilaire thermostat."""

    def __init__(self, interface, sn, nm, config):
        """Initialize the thermostat entity."""
        self._interface = interface
        self._sn = sn
        self._name = f"Aprilaire Thermostat {sn} ({nm})"
        self._current_temperature = None
        self._setpoint_cool_temperature = None
        self._setpoint_heat_temperature = None
        self._hvac_mode = HVACMode.OFF
        self._preset_mode = None
        self._polling_interval = config.data.get("polling_interval", 60) + random.randint(0, 10) # so all don't go at the same time
        self._bidrectional = config.data.get("bidirectional", False) 
        self._last_update = 0
        self._firsttime = True

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
            # cool setupoint cannot be lower than heat setpoint.
            if self._hvac_mode == HVACMode.COOL:
                await self._interface.set_setpoint(self._sn, HVACMode.COOL, target_temp)
                self._setpoint_cool_temperature = target_temp
                if self._setpoint_heat_temperature >= target_temp:
                    self._setpoint_heat_temperature = target_temp - 1
            elif self._hvac_mode == HVACMode.HEAT:
                await self._interface.set_setpoint(self._sn, HVACMode.HEAT, target_temp)
                self._setpoint_heat_temperature = target_temp
                if self._setpoint_cool_temperature <= target_temp:
                    self._setpoint_cool_temperature = target_temp + 1
            else:
                _LOGGER.error(f"Cannot set setpoint when mode is {self._hvac_mode} or not {self._setpoint_heat_temperature} < {target_temp} < {self._setpoint_cool_temperature}")
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


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):

        # Check if it's time to poll the thermostat
        current_time = time.time()
        if current_time - self._last_update < self._polling_interval:
            return  # Skip update if polling interval hasn't passed
        
        self._last_update = current_time

        """Fetch new data from the Aprilaire thermostat."""
        _LOGGER.debug(f"Updating Aprilaire thermostat {self._sn} at {current_time} ")

        # Get current temperature
        tt = await self._interface.get_temperature(self._sn)
        if tt:
            self._current_temperature = tt 

        #HACK FOR TESTING
        st = await self._interface.get_state(self._sn)
        if st:
            self._name = st

        if self._bidrectional or self._firsttime:
            # Need to get what is on the thermostats after initialization
            self._firsttime = False 

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

