"""Sensor platform for Stremio."""
from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

try:
    from stremio_api import StremioAPIClient
    _LOGGER.debug("Successfully imported StremioAPIClient in sensor.py")
except Exception as ex:
    _LOGGER.warning("Failed to import stremio_api in sensor.py. Error: %s", ex)
    class StremioAPIClient: pass

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stremio sensors."""
    _LOGGER.debug("Setting up Stremio sensors for entry: %s", entry.entry_id)
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    user = data["user"]

    async def async_update_data():
        """Fetch data from API."""
        _LOGGER.debug("Fetching Stremio data...")
        library = await client.get_library()
        continue_watching = await client.get_continue_watching()
        addons = await client.get_addons()
        
        # Fetch detailed meta for the first "continue watching" item
        meta = None
        if continue_watching:
            item = continue_watching[0]
            _LOGGER.debug("Found continue watching item: %s (%s)", item.name, item.id)
            try:
                meta = await client.get_meta(item.type, item.id)
                _LOGGER.debug("Fetched meta for %s: %s", item.name, "Success" if meta else "Failed")
            except Exception as ex:
                _LOGGER.error("Failed to fetch meta for %s: %s", item.name, ex)
            
        return {
            "library": library,
            "continue_watching": continue_watching,
            "addons": addons,
            "current_meta": meta,
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="stremio",
        update_method=async_update_data,
        update_interval=timedelta(minutes=15),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            StremioUserSensor(coordinator, entry, user),
            StremioLibrarySensor(coordinator, entry, user),
            StremioLibraryMoviesSensor(coordinator, entry, user),
            StremioLibrarySeriesSensor(coordinator, entry, user),
            StremioCurrentWatchingSensor(coordinator, entry, user),
            StremioCurrentWatchingCastSensor(coordinator, entry, user),
            StremioCurrentWatchingDirectorSensor(coordinator, entry, user),
            StremioCurrentWatchingRatingSensor(coordinator, entry, user),
            StremioCurrentWatchingGenresSensor(coordinator, entry, user),
            StremioCurrentWatchingDescriptionSensor(coordinator, entry, user),
            StremioAddonsCountSensor(coordinator, entry, user),
            StremioWatchTimeSensor(coordinator, entry, user),
            StremioLatestAdditionSensor(coordinator, entry, user),
        ]
    )

class StremioEntity(CoordinatorEntity):
    """Base class for Stremio entities."""

    def __init__(self, coordinator, entry, user):
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._user = user
        self._attr_device_info = {
            "identifiers": {(DOMAIN, user.id)},
            "name": f"Stremio ({user.fullname or user.email})",
            "manufacturer": "Stremio",
            "model": "Cloud Account",
            "sw_version": "1.0",
        }

class StremioUserSensor(StremioEntity, SensorEntity):
    """Sensor for Stremio User."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio User"
        self._attr_unique_id = f"{entry.entry_id}_user"

    @property
    def native_value(self) -> str:
        """Return the user name."""
        return self._user.fullname or self._user.email

    @property
    def extra_state_attributes(self):
        """Return user info."""
        return {
            "email": self._user.email,
            "id": self._user.id,
            "lang": self._user.lang,
        }

class StremioLibrarySensor(StremioEntity, SensorEntity):
    """Sensor for Stremio Library size."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Library Size"
        self._attr_unique_id = f"{entry.entry_id}_library_size"

    @property
    def native_value(self) -> int:
        """Return the size of the library."""
        return len(self.coordinator.data["library"])

    @property
    def extra_state_attributes(self):
        """Return library breakdown."""
        library = self.coordinator.data["library"]
        movies = [item for item in library if item.type == "movie"]
        series = [item for item in library if item.type == "series"]
        return {
            "movies_count": len(movies),
            "series_count": len(series),
            "other_count": len(library) - len(movies) - len(series)
        }

class StremioLibraryMoviesSensor(StremioEntity, SensorEntity):
    """Sensor for Stremio Movies in library."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Movies"
        self._attr_unique_id = f"{entry.entry_id}_library_movies"

    @property
    def native_value(self) -> int:
        """Return the count of movies."""
        return len([i for i in self.coordinator.data["library"] if i.type == "movie"])

class StremioLibrarySeriesSensor(StremioEntity, SensorEntity):
    """Sensor for Stremio Series in library."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Series"
        self._attr_unique_id = f"{entry.entry_id}_library_series"

    @property
    def native_value(self) -> int:
        """Return the count of series."""
        return len([i for i in self.coordinator.data["library"] if i.type == "series"])

class StremioCurrentWatchingSensor(StremioEntity, SensorEntity):
    """Sensor for Stremio's current/last watched item."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current Watching"
        self._attr_unique_id = f"{entry.entry_id}_current_watching"

    @property
    def native_value(self) -> str | None:
        """Return the name of the last watched item."""
        watching = self.coordinator.data["continue_watching"]
        if watching:
            return watching[0].name
        return None

    @property
    def extra_state_attributes(self):
        """Return attributes for the last watched item."""
        watching = self.coordinator.data["continue_watching"]
        if not watching:
            return {}
        
        item = watching[0]
        
        return {
            "type": item.type,
            "poster": item.poster,
            "season": item.state.season,
            "episode": item.state.episode,
            "last_watched": item.state.last_watched.isoformat() if item.state.last_watched else None
        }

class StremioAddonsCountSensor(StremioEntity, SensorEntity):
    """Sensor for Stremio Addon count."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Addons Installed"
        self._attr_unique_id = f"{entry.entry_id}_addons_count"

    @property
    def native_value(self) -> int:
        """Return the number of addons."""
        return len(self.coordinator.data["addons"])

    @property
    def extra_state_attributes(self):
        """Return list of addon names and resource counts."""
        addons = self.coordinator.data["addons"]
        
        resource_counts = {
            "stream": 0,
            "subtitles": 0,
            "meta": 0,
            "catalog": 0
        }
        
        for addon in addons:
            resources = addon.manifest.resources
            for res in resources:
                # Resources can be strings or objects with 'name'
                res_name = res if isinstance(res, str) else res.get("name") if isinstance(res, dict) else None
                if res_name in resource_counts:
                    resource_counts[res_name] += 1

        return {
            "addons": [addon.manifest.name for addon in addons],
            **resource_counts
        }

class StremioWatchTimeSensor(StremioEntity, SensorEntity):
    """Sensor for total Stremio watch time."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Total Watch Time"
        self._attr_unique_id = f"{entry.entry_id}_watch_time"
        self._attr_native_unit_of_measurement = "h"
        self._attr_state_class = "measurement"

    @property
    def native_value(self) -> float:
        """Return the total watch time in hours."""
        library = self.coordinator.data["library"]
        # overallTimeWatched is in ms
        total_ms = sum(item.state.overall_time_watched for item in library)
        return round(total_ms / (1000 * 60 * 60), 2)

class StremioLatestAdditionSensor(StremioEntity, SensorEntity):
    """Sensor for last item added to Stremio library."""

    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Latest Addition"
        self._attr_unique_id = f"{entry.entry_id}_latest_addition"

    @property
    def native_value(self) -> str | None:
        """Return the name of the latest item."""
        library = self.coordinator.data["library"]
        if not library:
            return None
        
        # Sort by ctime (created time)
        latest = sorted([i for i in library if i.ctime], key=lambda x: x.ctime, reverse=True)
        if latest:
            return latest[0].name
        return None

    @property
    def extra_state_attributes(self):
        """Return attributes for latest item."""
        library = self.coordinator.data["library"]
        if not library:
            return {}
            
        latest = sorted([i for i in library if i.ctime], key=lambda x: x.ctime, reverse=True)
        if not latest:
            return {}
            
        item = latest[0]
        return {
            "type": item.type,
            "poster": item.poster,
            "added_at": item.ctime.isoformat() if item.ctime else None
        }

class StremioCurrentWatchingCastSensor(StremioEntity, SensorEntity):
    """Sensor for Current Watching Cast."""
    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current Cast"
        self._attr_unique_id = f"{entry.entry_id}_current_cast"

    @property
    def native_value(self) -> str | None:
        meta = self.coordinator.data.get("current_meta")
        if meta and meta.cast:
            return ", ".join(meta.cast)
        return None

class StremioCurrentWatchingDirectorSensor(StremioEntity, SensorEntity):
    """Sensor for Current Watching Director."""
    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current Director"
        self._attr_unique_id = f"{entry.entry_id}_current_director"

    @property
    def native_value(self) -> str | None:
        meta = self.coordinator.data.get("current_meta")
        if meta and meta.director:
            return ", ".join(meta.director)
        return None

class StremioCurrentWatchingRatingSensor(StremioEntity, SensorEntity):
    """Sensor for Current Watching IMDb Rating."""
    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current IMDb Rating"
        self._attr_unique_id = f"{entry.entry_id}_current_rating"

    @property
    def native_value(self) -> str | None:
        meta = self.coordinator.data.get("current_meta")
        if meta and meta.imdb_rating:
            return meta.imdb_rating
        return None

class StremioCurrentWatchingGenresSensor(StremioEntity, SensorEntity):
    """Sensor for Current Watching Genres."""
    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current Genres"
        self._attr_unique_id = f"{entry.entry_id}_current_genres"

    @property
    def native_value(self) -> str | None:
        meta = self.coordinator.data.get("current_meta")
        if meta and meta.genres:
            return ", ".join(meta.genres)
        return None

class StremioCurrentWatchingDescriptionSensor(StremioEntity, SensorEntity):
    """Sensor for Current Watching Description."""
    def __init__(self, coordinator, entry, user):
        super().__init__(coordinator, entry, user)
        self._attr_name = "Stremio Current Description"
        self._attr_unique_id = f"{entry.entry_id}_current_description"

    @property
    def native_value(self) -> str | None:
        meta = self.coordinator.data.get("current_meta")
        if meta and meta.description:
            return meta.description
        return None
