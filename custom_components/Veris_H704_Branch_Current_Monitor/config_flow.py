
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_BAUDRATE, CONF_SLAVE_ID, DEFAULT_BAUDRATE, DEFAULT_SLAVE_ID, DEFAULT_PORT
from .veris_modbus_interface import VerisModbusInterface

_LOGGER = logging.getLogger(__name__)

class VerisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the configuration flow for the Veris Branch Power Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Step to configure the integration via UI."""
        errors = {}

        if user_input is not None:
            port = user_input[CONF_PORT]
            baudrate = user_input[CONF_BAUDRATE]
            slave_id = user_input[CONF_SLAVE_ID]

            # Attempt to connect to verify settings
            modbus_interface = VerisModbusInterface(port, baudrate, slave_id)
            if await modbus_interface.connect():
                await modbus_interface.close()

                return self.async_create_entry(
                    title=f"Veris Power Monitor ({port})",
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        # Show form for user to input settings
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PORT, default=DEFAULT_PORT): str,
                vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
                vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
            }),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Handle reconfiguration of an existing integration."""
        return await self.async_step_user(user_input)
