"""Media Source for Stremio."""
from __future__ import annotations

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN

try:
    from stremio_api import StremioAPIClient
except ImportError:
    class StremioAPIClient: pass

async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    """Set up the Stremio media source."""
    return StremioMediaSource(hass)

class StremioMediaSource(MediaSource):
    """Media source for Stremio library."""

    name: str = "Stremio"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Browse media."""
        if item.identifier is None:
            return self._build_root_browser()

        # Simple browsing: root -> types -> items
        if item.identifier == "movies":
            return await self._build_type_browser("movie", "Movies")
        if item.identifier == "series":
            return await self._build_type_browser("series", "TV Shows")
        
        return self._build_root_browser()

    def _build_root_browser(self) -> BrowseMediaSource:
        """Build the root browser."""
        root = BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.CHANNELS,
            title="Stremio",
            can_play=False,
            can_browse=True,
            children_media_class=MediaClass.DIRECTORY,
        )
        root.children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier="movies",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.CHANNELS,
                title="Movies",
                can_play=False,
                can_browse=True,
            ),
            BrowseMediaSource(
                domain=DOMAIN,
                identifier="series",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.CHANNELS,
                title="TV Shows",
                can_play=False,
                can_browse=True,
            ),
        ]
        return root

    async def _build_type_browser(self, content_type: str, title: str) -> BrowseMediaSource:
        """Build browser for a specific type."""
        # Get the first client
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return self._build_root_browser()
        
        data = self.hass.data[DOMAIN][entries[0].entry_id]
        client = data["client"]
        library = await client.get_library()
        
        filtered = [item for item in library if item.type == content_type]

        browser = BrowseMediaSource(
            domain=DOMAIN,
            identifier=content_type,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.CHANNELS,
            title=title,
            can_play=False,
            can_browse=True,
        )
        
        browser.children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"item_{item.id}",
                media_class=MediaClass.MOVIE if content_type == "movie" else MediaClass.TV_SHOW,
                media_content_type=MediaType.VIDEO,
                title=item.name,
                can_play=True,
                can_browse=False,
                thumbnail=item.poster,
            )
            for item in filtered
        ]
        return browser

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a URL (placeholder for now as we don't handle streaming directly yet)."""
        # This would eventually return a stream URL from an addon
        return PlayMedia("", "video/mp4")
