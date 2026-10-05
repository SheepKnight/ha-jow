"""Async API client for Jow using aiohttp."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp

from .const import AUTH_URL, BASE_API_URL

_LOGGER = logging.getLogger(__name__)


class JowApiError(Exception):
    """Base exception for Jow API errors."""


class JowAuthError(JowApiError):
    """Authentication failure exception."""


class JowConnectionError(JowApiError):
    """Network or connection error exception."""


class JowApiClient:
    """API client for Jow."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        device_id: str,
        refresh_token: str,
    ) -> None:
        """Initialize the Jow API client."""
        self._session = session
        self.device_id = device_id
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None

    def _default_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://jow.fr",
            "Referer": "https://jow.fr/",
            "x-jow-web-version": "21.7.4",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def async_refresh_access_token(self) -> str:
        """Exchange the refresh token and device ID for a fresh access token."""
        payload = {
            "deviceId": self.device_id,
            "refreshToken": self.refresh_token,
        }

        try:
            async with self._session.post(
                AUTH_URL,
                json=payload,
                headers=self._default_headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (400, 401, 403):
                    body = await resp.text()
                    _LOGGER.error("Jow authentication failed (%d): %s", resp.status, body)
                    raise JowAuthError(f"Authentication failed: status {resp.status}")

                resp.raise_for_status()
                data = await resp.json()

        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as err:
            raise JowConnectionError(f"Connection error during auth: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise JowApiError(f"HTTP error during auth: {err}") from err

        token = data.get("accessToken") or data.get("data", {}).get("accessToken")
        if not token:
            raise JowAuthError(f"No access token in response: {data}")

        self.access_token = token

        # Store rotated refresh token if provided
        new_refresh = data.get("refreshToken") or data.get("data", {}).get("refreshToken")
        if new_refresh:
            self.refresh_token = new_refresh

        return self.access_token

    async def async_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True,
    ) -> Dict[str, Any]:
        """Send an authenticated request to Jow API with automatic 401 retry."""
        if not self.access_token:
            await self.async_refresh_access_token()

        url = f"{BASE_API_URL}/{path.lstrip('/')}"
        headers = self._default_headers()

        try:
            async with self._session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 401 and retry_on_401:
                    _LOGGER.debug("Access token expired, refreshing...")
                    await self.async_refresh_access_token()
                    return await self.async_request(
                        method=method,
                        path=path,
                        params=params,
                        json_data=json_data,
                        retry_on_401=False,
                    )

                if resp.status in (401, 403):
                    raise JowAuthError(f"Unauthorized request to {path}")

                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", data)

        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as err:
            raise JowConnectionError(f"Connection error to {url}: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise JowApiError(f"HTTP error ({err.status}) on {url}: {err}") from err

    async def async_get_letscook(
        self,
        preferred_limit: int = 20,
        projection_fields: Optional[List[str]] = None,
        zone_id: str = "FR",
    ) -> Dict[str, Any]:
        """Fetch user letscook data (collections, menus, recipes to cook, shared)."""
        if projection_fields is None:
            projection_fields = [
                "collections",
                "pendingMenu",
                "recipesToCook",
                "sharedRecipes",
                "uploaded",
            ]

        params = {
            "preferredLimit": preferred_limit,
            "projectionFields": ",".join(projection_fields),
            "availabilityZoneId": zone_id,
        }
        return await self.async_request("GET", "profile/letscook", params=params)

    async def async_get_profile(self) -> Dict[str, Any]:
        """Fetch user unified profile information."""
        params = {
            "needsProviderProfile": "true",
            "platform": "web",
            "deviceId": self.device_id,
        }
        return await self.async_request("GET", "profile/unified", params=params)
