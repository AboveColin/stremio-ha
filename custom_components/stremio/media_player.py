"""Media Player platform for Stremio."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.components import media_source
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from datetime import timedelta
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("Setting up Stremio media player for entry: %s", entry.entry_id)
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    user = data["user"]

    async def async_update_data():
        """Fetch data from API."""
        _LOGGER.debug("Fetching Stremio media player data...")
        continue_watching = await client.get_continue_watching()
        
        # Fetch detailed meta for the first "continue watching" item
        meta = None
        if continue_watching:
            item = continue_watching[0]
            _LOGGER.debug("Media Player found item: %s (%s)", item.name, item.id)
            try:
                meta = await client.get_meta(item.type, item.id)
                _LOGGER.debug("Media Player fetched meta for %s: %s", item.name, "Success" if meta else "Failed")
            except Exception as ex:
                _LOGGER.error("Media Player failed to fetch meta for %s: %s", item.name, ex)
            
        return {
            "continue_watching": continue_watching,
            "current_meta": meta,
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="stremio_media_player",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([StremioMediaPlayer(coordinator, entry, user)])

class StremioMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media player for Stremio."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_has_entity_name = True
    _attr_name = "Stremio"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, user: Any) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._user = user
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_supported_features = (
            MediaPlayerEntityFeature.BROWSE_MEDIA
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, user.id)},
            "name": f"Stremio ({user.fullname or user.email})",
            "manufacturer": "",
            "model": "Cloud Account",
            "sw_version": "1.0",
        }

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            item = watching[0]
            if item.state.last_watched:
                now = dt_util.utcnow()
                # If watched in the last 15 minutes, consider it playing
                if (now - item.state.last_watched).total_seconds() < 900:
                    return MediaPlayerState.PLAYING
            return MediaPlayerState.IDLE
        return MediaPlayerState.OFF

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            return watching[0].name
        return None

    @property
    def media_image_url(self) -> str | None:
        """Image URL of current playing media."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            return watching[0].poster
        return None

    @property
    def media_content_type(self) -> MediaType | str | None:
        """Content type of current playing media."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            ctype = watching[0].type
            if ctype == "movie":
                return MediaType.MOVIE
            if ctype == "series":
                return MediaType.TVSHOW
        return None

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        meta = self.coordinator.data.get("current_meta")
        if not meta:
            return None
            
        parts = []
        if meta.director:
             parts.append(f"Director: {', '.join(meta.director)}")
        if meta.cast:
             parts.append(f"Cast: {', '.join(meta.cast[:3])}")
            
        return " | ".join(parts) if parts else None

    @property
    def media_series_title(self) -> str | None:
        """Title of series of current playing media, TV show only."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].type == "series":
            return watching[0].name
        return None

    @property
    def media_season(self) -> str | None:
        """Season of current playing media, TV show only."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].state:
            return str(watching[0].state.season)
        return None

    @property
    def media_episode(self) -> str | None:
        """Episode of current playing media, TV show only."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].state and watching[0].state.episode:
            return str(watching[0].state.episode)
        return None

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].state and watching[0].state.duration:
            return int(watching[0].state.duration / 1000)
        return None

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].state:
            return int(watching[0].state.time_offset / 1000)
        return None

    @property
    def media_position_updated_at(self):
        """When the position was last updated."""
        watching = self.coordinator.data["continue_watching"]
        if watching and watching[0].state and watching[0].state.last_watched:
            return watching[0].state.last_watched
        return None

    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            return watching[0].id
        return None

    @property
    def app_name(self) -> str | None:
        """Name of the current running app."""
        return "Stremio"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        meta = self.coordinator.data.get("current_meta")
        if not meta:
            return {}
        
        return {
            "cast": meta.cast,
            "director": meta.director,
            "writer": meta.writer,
            "genres": meta.genres,
            "imdb_rating": meta.imdb_rating,
            "awards": meta.awards,
            "runtime": meta.runtime,
            "description": meta.description,
        }

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith("video/"),
        )

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            _LOGGER.info("Stremio Media Player resolving: %s -> %s", media_id, play_item.url)
            # For now, we just log it as there is no physical device to target.
            # In a real scenario, this would send the URL to a Chromecast/Android TV.
        else:
            _LOGGER.warning("Non-media-source playback not supported: %s", media_id)
