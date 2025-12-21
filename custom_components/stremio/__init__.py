"""The Stremio integration."""
from __future__ import annotations

import logging
import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, CONF_AUTH_KEY
try:
    from stremio_api import StremioAPIClient
    _LOGGER.debug("Successfully imported StremioAPIClient in __init__.py")
except Exception as ex:
    _LOGGER.warning("Failed to import stremio_api in __init__.py. Error: %s", ex)
    if 'StremioAPIError' not in locals():
        class StremioAPIError(Exception): pass
    
    class StremioAPIClient:
        def __init__(self, *args, **kwargs): pass
        async def get_addons(self): return []
        async def get_user(self): return None


PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.MEDIA_PLAYER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stremio from a config entry."""
    auth_key = entry.data[CONF_AUTH_KEY]
    
    from homeassistant.helpers.httpx_client import get_async_client
    session = get_async_client(hass)
    client = StremioAPIClient(auth_key, client=session)
    
    # Verify the session exists immediately and get user info
    from homeassistant.exceptions import ConfigEntryNotReady
    try:
        user = await client.get_user()
    except Exception as ex:
        _LOGGER.error("Stremio authentication failed or session expired: %s", ex)
        raise ConfigEntryNotReady from ex

    # Store the client and user in hass data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "user": user,
    }

    async def handle_get_streams(call):
        """Handle the get_streams service call."""
        content_type = call.data.get("type")
        content_id = call.data.get("id")
        
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        addons = await client.get_addons()
        streams = []
        
        for addon in addons:
            manifest = addon.manifest
            supports_type = content_type in manifest.types
            has_stream = any(
                res == "stream" or (isinstance(res, dict) and res.get("name") == "stream")
                for res in manifest.resources
            )
            
            if supports_type and has_stream:
                try:
                    base_url = addon.transport_url.replace("/manifest.json", "")
                    url = f"{base_url}/stream/{content_type}/{content_id}.json"
                    async with httpx.AsyncClient() as hclient:
                        resp = await hclient.get(url, timeout=5.0)
                        if resp.status_code == 200:
                            addon_streams = resp.json().get("streams", [])
                            for s in addon_streams:
                                s["addon_name"] = manifest.name
                            streams.extend(addon_streams)
                except Exception as e:
                    _LOGGER.warning("Failed to fetch streams from %s: %s", manifest.name, e)

        _LOGGER.info("Found %s streams for %s", len(streams), content_id)
        hass.bus.async_fire(f"{DOMAIN}_streams_received", {"streams": streams})

    hass.services.async_register(DOMAIN, "get_streams", handle_get_streams)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
