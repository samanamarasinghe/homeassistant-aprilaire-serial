import logging
import serial  # For serial communication
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    TEMP_FAHRENHEIT,
    CONF_NAME,
)

from . import DOMAIN

COMMAND_TEMP = "TEMP"
COMMAND_MODE = "MODE"
COMMAND_SETPOINT_HEAT = "SETPOINTHEAT"
COMMAND_SETPOINT_COOL = "SETPOINTCOOL"

APRILAIRE_MODES = {
    "A": "auto",
    "C": HVAC_MODE_COOL,
    "H": HVAC_MODE_HEAT,
    "OFF": HVAC_MODE_OFF,
}

class AprilaireThermostat(ClimateEntity):
    """Representation of an Aprilaire thermostat."""

    def __init__(self, serial_connection, name: str, address: int):
        """Initialize the thermostat."""
        self._serial_connection = serial_connection
        self._name = name
        self._address = address
        self._current_temperature = None
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temperature = None
        self._supported_features = SUPPORT_TARGET_TEMPERATURE

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def supported_features(self):
        """Return the supported features."""
        return self._supported_features

    def set_temperature(self, **kwargs):
        """Set the target temperature."""
        self._target_temperature = kwargs.get("temperature")
        if self._hvac_mode == HVAC_MODE_HEAT:
            self._send_command(f"SETPOINTHEAT={int(self._target_temperature)}")
        elif self._hvac_mode == HVAC_MODE_COOL:
            self._send_command(f"SETPOINTCOOL={int(self._target_temperature)}")

    def set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        mode = {v: k for k, v in APRILAIRE_MODES.items()}.get(hvac_mode, "OFF")
        self._send_command(f"MODE={mode}")
        self._hvac_mode = hvac_mode

    def update(self):
        """Fetch new state data from the thermostat."""
        self._current_temperature = self._get_command_response("TEMP?")
        self._hvac_mode = APRILAIRE_MODES.get(self._get_command_response("MODE?"), HVAC_MODE_OFF)

    def _send_command(self, command: str):
        """Send a command to the thermostat."""
        full_command = f"SN{self._address} {command}\r"
        self._serial_connection.write(full_command.encode("utf-8"))

    def _get_command_response(self, command: str):
        """Send a command and return the response."""
        self._send_command(command)
        response = self._serial_connection.readline().decode("utf-8").strip()
        return response.split("=")[-1] if "=" in response else None


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Aprilaire thermostats from a config entry."""
    serial_connection = hass.data[DOMAIN]["serial_connection"]
    # Example: Define multiple thermostats (change as needed)
    thermostats = [
        AprilaireThermostat(serial_connection, "Thermostat 1", address=1),
        AprilaireThermostat(serial_connection, "Thermostat 2", address=2),
    ]
    async_add_entities(thermostats, update_before_add=True)

