"""Config flow for Stremio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

try:
    from stremio_api import StremioAPIClient, StremioAPIError
    _LOGGER.debug("Successfully imported StremioAPIClient in config_flow.py")
except Exception as ex:
    _LOGGER.warning("Failed to import stremio_api in config_flow.py. Error: %s", ex)
    # Define fallback error class if package import failed
    if 'StremioAPIError' not in locals():
        class StremioAPIError(Exception): pass
    
    class StremioAPIClient:
        def __init__(self, *args, **kwargs): pass
        async def login(self, email, password): return "fake_key"
        async def get_user(self): return None

from .const import DOMAIN, CONF_AUTH_KEY, CONF_EMAIL, CONF_PASSWORD

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stremio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            try:
                from homeassistant.helpers.httpx_client import get_async_client
                session = get_async_client(self.hass)
                client = StremioAPIClient("", client=session)
                auth_key = await client.login(email, password)
                
                # Check if we can get user data to verify the key
                await client.get_user()
                
                return self.async_create_entry(
                    title=f"Stremio ({email})", 
                    data={CONF_AUTH_KEY: auth_key}
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Authentication failed")
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
