from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.util.unit_system import UnitOfTemperature
import logging
from .aprilair_serial_interface import AprilaireThermostatSerialInterface
from .const import ATTR_TEMPERATURE
from homeassistant.util import Throttle
from datetime import timedelta

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

# not sure how HVACMode.HEAT_COOL and HVACMode.AUTO works with the thermostat card
SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY] 

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup climate entities for Aprilaire thermostats."""
    port = config_entry.data.get("port", "/dev/ttyUSB0")
    baudrate = config_entry.data.get("baudrate", 9600)
    interface = AprilaireThermostatSerialInterface(port, baudrate)
    unused = config_entry.data.get("polling_interval", 60) 

    # Establish the connection
    try:
        await interface.connect()
    except Exception as e:
        _LOGGER.error(f"Failed to connect to serial device: {e}")
        return
    
    # use the connection
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
        self._hvac_action = HVACAction.OFF
        self._preset_mode = None
        self._bidrectional = config.data.get("bidirectional", False) 
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
        try:
            return float(self._current_temperature)
        except:
            _LOGGER.error(f": {self._current_temperature} connot be made a temprature")
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if self._hvac_mode == HVACMode.COOL:
            temp = self._setpoint_cool_temperature
        elif self._hvac_mode == HVACMode.HEAT:
            temp = self._setpoint_heat_temperature
        else:
            return None
        try:
            return float(temp)
        except:
            _LOGGER.error(f": {temp} connot be made a temprature")
            return None

    @property
    def target_temperature_high(self):
        try:
            return float(self._setpoint_heat_temperature)
        except:
            _LOGGER.error(f": {self._setpoint_heat_temperature} connot be made a temprature")
            return None

    @property
    def target_temperature_low(self) -> float | None:
        try:
            return float(self._setpoint_cool_temperature)
        except:
            _LOGGER.error(f": {self._setpoint_cool_temperature} connot be made a temprature")
            return None

    @property
    def hvac_mode(self): 
        """Return the current HVAC mode."""
        return self._hvac_mode
    
    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        return self._attr_hvac_action

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

            self._target_temperature = target_temp
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
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, mode):
        """Set the HVAC mode for the thermostat."""
        if mode not in SUPPORTED_HVAC_MODES:
            _LOGGER.error("Unsupported HVAC mode: %s", mode)
            return
        
        self._hvac_mode = mode
        await self._interface.set_mode(self._sn, mode)
        self.async_write_ha_state()

    def state2action(self, state):
        try:
            if state[state.find("W1")+2] == "+":
                if state[state.find("G")+1] == "+":
                    return HVACAction.HEATING
                else:
                    return HVACAction.PREHEATING
            elif state[state.find("Y1")+2] == "+":
                return HVACAction.COOLING
            elif state[state.find("G")+1] == "+":
                return HVACAction.FAN
            elif self._hvac_mode == HVACMode.OFF:
                return HVACAction.OFF
            else:
                return HVACAction.IDLE
        except:
            _LOGGER.error(f"For {self._sn} could not convert {state} to action ")
            return None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Fetch new data from the Aprilaire thermostat."""
        #_LOGGER.debug(f"Updating Aprilaire thermostat {self._sn} ")

        # Get current temperature
        tt = await self._interface.get_temperature(self._sn)
        if tt:
            self._current_temperature = tt 

        #Get the current state
        st = await self._interface.get_state(self._sn)
        if st:
            self._hvac_action = self.state2action(st)

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

