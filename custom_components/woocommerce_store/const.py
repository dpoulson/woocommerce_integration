"""Constants for WooCommerce Store integration."""
from typing import Final

DOMAIN: Final = "woocommerce_store"

# Configuration keys
CONF_URL: Final = "url"
CONF_CONSUMER_KEY: Final = "consumer_key"
CONF_CONSUMER_SECRET: Final = "consumer_secret"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes
DEFAULT_VERIFY_SSL: Final = True

# Platforms
PLATFORMS: Final = ["sensor"]

# Services
SERVICE_REFRESH: Final = "refresh"
