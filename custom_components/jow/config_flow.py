"""Config flow for Jow integration supporting web view and manual login."""

import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JowApiClient, JowAuthError, JowConnectionError
from .const import CONF_DEVICE_ID, CONF_REFRESH_TOKEN, DOMAIN
from .view import VIEW_LOGIN_URL, ensure_views_registered

_LOGGER = logging.getLogger(__name__)

STEP_MANUAL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_REFRESH_TOKEN): str,
    }
)


class JowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - choose between web view helper and manual."""
        ensure_views_registered(self.hass)

        # If user already used the web login helper and tokens are waiting, offer direct confirmation
        pending_auth = self.hass.data.get(DOMAIN, {}).get("latest_web_auth")
        if pending_auth:
            return await self.async_step_confirm_web(pending_auth)

        return self.async_show_menu(
            step_id="user",
            menu_options=["webview", "manual"],
        )

    async def async_step_webview(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Guide user through the browser web view / bookmarklet login."""
        ensure_views_registered(self.hass)
        errors: Dict[str, str] = {}


        if user_input is not None:
            pending_auth = self.hass.data.get(DOMAIN, {}).get("latest_web_auth")
            if not pending_auth:
                errors["base"] = "web_auth_pending"
            else:
                return await self._create_jow_entry(
                    device_id=pending_auth[CONF_DEVICE_ID],
                    refresh_token=pending_auth[CONF_REFRESH_TOKEN],
                    user_name=pending_auth.get("user_name"),
                )

        return self.async_show_form(
            step_id="webview",
            data_schema=vol.Schema({}),
            description_placeholders={"login_url": VIEW_LOGIN_URL},
            errors=errors,
        )

    async def async_step_confirm_web(
        self, pending_auth: Dict[str, Any]
    ) -> FlowResult:
        """Confirm entry creation when credentials were sent via web helper."""
        return await self._create_jow_entry(
            device_id=pending_auth[CONF_DEVICE_ID],
            refresh_token=pending_auth[CONF_REFRESH_TOKEN],
            user_name=pending_auth.get("user_name"),
        )

    async def async_step_manual(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle manual credential entry."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            refresh_token = user_input[CONF_REFRESH_TOKEN].strip()

            try:
                user_name = await self._validate_credentials(device_id, refresh_token)
            except JowAuthError:
                errors["base"] = "invalid_auth"
            except JowConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during manual setup")
                errors["base"] = "unknown"
            else:
                return await self._create_jow_entry(
                    device_id=device_id,
                    refresh_token=refresh_token,
                    user_name=user_name,
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_MANUAL_SCHEMA,
            errors=errors,
        )

    async def _validate_credentials(self, device_id: str, refresh_token: str) -> str:
        """Validate credentials against Jow API and return user display name."""
        session = async_get_clientsession(self.hass)
        client = JowApiClient(session, device_id=device_id, refresh_token=refresh_token)
        await client.async_refresh_access_token()
        profile = await client.async_get_profile()
        return (
            profile.get("jowProfile", {}).get("firstName")
            or profile.get("jowProfile", {}).get("email")
            or "Jow User"
        )

    async def _create_jow_entry(
        self, device_id: str, refresh_token: str, user_name: Optional[str] = None
    ) -> FlowResult:
        """Register unique_id and create entry."""
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        # Clean up consumed web auth
        if DOMAIN in self.hass.data and "latest_web_auth" in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN].pop("latest_web_auth", None)

        title = f"Jow ({user_name})" if user_name else "Jow"
        return self.async_create_entry(
            title=title,
            data={
                CONF_DEVICE_ID: device_id,
                CONF_REFRESH_TOKEN: refresh_token,
            },
        )
