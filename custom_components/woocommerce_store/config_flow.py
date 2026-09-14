"""Config flow for WooCommerce Store integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    WooCommerceApiClient,
    WooCommerceAuthError,
    WooCommerceConnectionError,
)
from .const import (
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_UPDATE_INTERVAL,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_CONSUMER_KEY): str,
        vol.Required(CONF_CONSUMER_SECRET): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user credentials by testing API connection."""
    session = async_get_clientsession(hass, verify_ssl=data.get(CONF_VERIFY_SSL, True))
    client = WooCommerceApiClient(
        url=data[CONF_URL],
        consumer_key=data[CONF_CONSUMER_KEY],
        consumer_secret=data[CONF_CONSUMER_SECRET],
        session=session,
        verify_ssl=data.get(CONF_VERIFY_SSL, True),
    )

    await client.test_connection()
    parsed = urlparse(client.base_url)
    title = parsed.netloc or client.base_url
    return {"title": title}


class WooCommerceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WooCommerce Store."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            user_input[CONF_URL] = url

            try:
                info = await validate_input(self.hass, user_input)
            except WooCommerceAuthError:
                errors["base"] = "invalid_auth"
            except WooCommerceConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during WooCommerce validation")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(url.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WooCommerceOptionsFlowHandler:
        """Get the options flow for this handler."""
        return WooCommerceOptionsFlowHandler(config_entry)


class WooCommerceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle WooCommerce options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=30, max=86400)),
                }
            ),
        )
