"""The Jow Home Assistant integration."""

import json
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JowApiClient
from .const import CONF_DEVICE_ID, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import JowDataUpdateCoordinator
from .todo import format_recipe
from .view import ensure_views_registered

_LOGGER = logging.getLogger(__name__)

# Platforms supported
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.TODO]

SERVICE_GET_RECIPES = "get_recipes"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Jow component."""
    ensure_views_registered(hass)

    async def handle_get_recipes(call: ServiceCall) -> ServiceResponse:
        """Handle get_recipes action returning recipes as JSON."""
        category = call.data.get("category", "recipes_to_cook")
        recipes = []
        domain_data = hass.data.get(DOMAIN, {})
        for coordinator in domain_data.values():
            if isinstance(coordinator, JowDataUpdateCoordinator) and coordinator.data:
                letscook = coordinator.data.get("letscook", {})
                if category in ("recipes_to_cook", "all"):
                    to_cook = (
                        letscook.get("recipesToCook", {}).get("meals")
                        or letscook.get("recipesToCook", {}).get("recipes")
                        or []
                    )
                    recipes.extend([format_recipe(m) for m in to_cook])
                if category in ("pending_menu", "all"):
                    pending = (
                        letscook.get("pendingMenu", {}).get("meals")
                        or letscook.get("pendingMenu", {}).get("recipes")
                        or []
                    )
                    recipes.extend([format_recipe(m) for m in pending])
                break

        return {
            "count": len(recipes),
            "recipes": recipes,
            "recipes_json": json.dumps(recipes, ensure_ascii=False),
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RECIPES,
        handle_get_recipes,
        schema=vol.Schema({
            vol.Optional("category", default="recipes_to_cook"): vol.In(
                ["recipes_to_cook", "pending_menu", "all"]
            ),
        }),
        supports_response=SupportsResponse.ONLY,
    )

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
