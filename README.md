# Stremio for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)

Integrate [Stremio](https://www.stremio.com/) into Home Assistant. This integration allows you to track your library, see what you are currently watching, and browse your Stremio content directly from Home Assistant.

> [!IMPORTANT]
> This is an **unofficial** integration and is not affiliated with or endorsed by Stremio.

## Features

- **Media Player**:
  - Displays the current or last watched item from your "Continue Watching" list.
  - Shows poster, title, season, episode, and progress.
  - **Media Source**: Browse your Stremio library (Movies & Series) directly from the HA Media Browser.
- **Sensors**:
  - **User**: Name and email of the logged-in user.
  - **Library**: Total count of items, movies, and series in your library.
  - **Current Watching**: Detailed sensor for the item currently being played.
  - **Watch Time**: Total time spent watching (in hours).
  - **Addons**: Count and list of installed addons.
  - **Metadata**: Detailed sensors for Cast, Director, IMDb Rating, Genres, and Description of the current item.
- **Services**:
  - `stremio.get_streams`: Fetch available stream links for a specific content ID. Note: Results are fired as a `stremio_streams_received` event.

## Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add `https://github.com/AboveColin/stremio-ha` as a **Integration** repository. (Or search for "Stremio" if it has been added to the default store).
4. Click **Add** and then install the **Stremio** integration.
5. Restart Home Assistant.

### Manual

1. Download the latest release.
2. Copy the `custom_components/stremio` folder into your Home Assistant's `custom_components` directory.
   - *Note: Ensure the structure is `custom_components/stremio/__init__.py`, etc.*
3. Restart Home Assistant.

## Setup

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Stremio**.
3. Enter your Stremio **Email** and **Password**.
4. The integration will automatically discover your account and create the necessary entities.

## Future Plans

- [ ] Support for triggering playback on remote Stremio instances (Android TV, Desktop).
- [ ] Direct stream resolution and playback in Home Assistant.

## Credits

- Data provided by [Stremio API](https://www.stremio.com/).
- Built using the [stremio-api](https://pypi.org/project/stremio-api/) Python package.

---
Created and maintained by [@AboveColin](https://github.com/AboveColin)
