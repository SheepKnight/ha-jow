"""The Jow Home Assistant integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JowApiClient
from .const import CONF_DEVICE_ID, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import JowDataUpdateCoordinator
from .view import JowLoginView, JowCallbackView

_LOGGER = logging.getLogger(__name__)

# Platforms we will support (e.g. sensor, todo)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Jow component."""
    hass.data.setdefault(DOMAIN, {})

    # Register web login views
    hass.http.register_view(JowLoginView())
    hass.http.register_view(JowCallbackView())

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jow from a config entry."""
    hass.data.setdefault(DOMAIN, {})


    device_id = entry.data[CONF_DEVICE_ID]
    refresh_token = entry.data[CONF_REFRESH_TOKEN]

    session = async_get_clientsession(hass)
    client = JowApiClient(session, device_id=device_id, refresh_token=refresh_token)
    coordinator = JowDataUpdateCoordinator(hass, client)

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
