"""DataUpdateCoordinator for Jow integration."""

from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import JowApiClient, JowAuthError, JowConnectionError, JowApiError
from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)


class JowDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Jow data from the API."""

    def __init__(self, hass: HomeAssistant, client: JowApiClient) -> None:
        """Initialize coordinator."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Jow API."""
        try:
            # Fetch letscook data and user profile concurrently or sequentially
            letscook_data = await self.client.async_get_letscook()
            
            # Profile data
            try:
                profile_data = await self.client.async_get_profile()
            except Exception as err:
                _LOGGER.debug("Profile fetch failed, continuing with letscook data: %s", err)
                profile_data = {}

            return {
                "letscook": letscook_data,
                "profile": profile_data,
            }

        except JowAuthError as err:
            # Trigger Home Assistant reauth flow
            raise ConfigEntryAuthFailed(f"Authentication token expired: {err}") from err
        except (JowConnectionError, JowApiError) as err:
            raise UpdateFailed(f"Error communicating with Jow API: {err}") from err
