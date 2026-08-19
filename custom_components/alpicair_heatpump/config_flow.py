"""Config flow for the AlpicAir Heatpump integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DEFAULT_NAME,
    DEFAULT_BAUDRATE,
    CONF_SLAVE,
    CONF_CONNECTION_TYPE,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_CONNECTION_TYPE, default="tcp"): vol.In(["tcp", "serial"]),
        vol.Optional(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SERIAL_PORT, default="/dev/ttyUSB0"): str,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
        vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
    }
)


class AlpicAirHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AlpicAir Heatpump.

    The unit's native protocol is Modbus RTU over RS-485 (9600 8N1), but many
    installations bridge it to Modbus TCP with a serial gateway. Both are
    supported: pick "tcp" (host/port) or "serial" (serial_port/baudrate).
    """

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            conn_type = user_input[CONF_CONNECTION_TYPE]
            if conn_type == "tcp" and not user_input.get(CONF_HOST):
                errors["host"] = "required"
            elif conn_type == "serial" and not user_input.get(CONF_SERIAL_PORT):
                errors["serial_port"] = "required"

            if not errors:
                if conn_type == "tcp":
                    unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_SLAVE]}"
                else:
                    unique_id = f"{user_input[CONF_SERIAL_PORT]}:{user_input[CONF_SLAVE]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
