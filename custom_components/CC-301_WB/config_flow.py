"""Config flow for Gran-Electro CC-301-old integration."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries, exceptions
from .const import DOMAIN
import platform
import subprocess


def ping(host) -> bool:
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
    return subprocess.call(command) == 0


DATA_SCHEMA = vol.Schema({"device_name": str,
                          "device_id": str,
                          "host": str,
                          "port": str,
                          "slave_id": int,
                          "count_of_coils": int})


async def validate_input(data: dict) -> dict[str, Any]:
    """ Raise InvalidHost exception if ping failed"""
    if not ping(data["host"]):
        raise InvalidHost
    return {"title": f'CC-301&WB {data["host"]}'}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This connection class uses PUSH, as the hub will notify HA of changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}
        if user_input is not None:
            try:
                title = await validate_input(user_input)

                return self.async_create_entry(title=title["title"], data=user_input)
            except InvalidHost:
                errors["host"] = "invalid_host"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
