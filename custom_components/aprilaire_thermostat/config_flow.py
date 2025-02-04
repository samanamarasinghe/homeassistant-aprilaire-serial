import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

class AprilaireThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aprilaire thermostat integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the user input (port and baud rate)
            port = user_input.get("port")
            baudrate = user_input.get("baudrate")

            if not port or not baudrate:
                errors["base"] = "missing_data"
            else:
                # Save configuration and proceed
                return self.async_create_entry(
                    title="Aprilaire Thermostat",
                    data=user_input
                )

        # Show the form if no input or validation failed
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("port", default="/dev/ttyUSB0"): str,
                    vol.Required("baudrate", default=9600): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Define the options flow handler."""
        return AprilaireThermostatOptionsFlowHandler(config_entry)

class AprilaireThermostatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Aprilaire integration."""

    def __init__(self, config_entry):
        """Initialize Aprilaire options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Save updated options
            return self.async_create_entry(title="", data=user_input)

        # Show options form
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("polling_interval", default=60): int,
                }
            ),
        )
