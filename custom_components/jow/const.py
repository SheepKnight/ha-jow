"""Constants for the Jow integration."""

from typing import Final

DOMAIN: Final = "jow"

# Configuration keys
CONF_DEVICE_ID: Final = "device_id"
CONF_REFRESH_TOKEN: Final = "refresh_token"

# Defaults
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 30

# API endpoints
AUTH_URL: Final = "https://api.jow.fr/public/auth?createIfNotExist=true"
BASE_API_URL: Final = "https://api.jow.fr/public"
