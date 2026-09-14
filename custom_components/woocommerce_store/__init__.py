"""The WooCommerce Store integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WooCommerceApiClient, WooCommerceApiError
from .const import (
    ATTR_ORDER_ID,
    ATTR_PRODUCT_ID,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_UPDATE_INTERVAL,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
    SERVICE_GET_ORDER,
    SERVICE_GET_PRODUCT,
    SERVICE_REFRESH,
)
from .coordinator import WooCommerceDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WooCommerce Store from a config entry."""
    session = async_get_clientsession(
        hass,
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    client = WooCommerceApiClient(
        url=entry.data[CONF_URL],
        consumer_key=entry.data[CONF_CONSUMER_KEY],
        consumer_secret=entry.data[CONF_CONSUMER_SECRET],
        session=session,
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    update_interval_sec = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )

    coordinator = WooCommerceDataUpdateCoordinator(
        hass,
        client=client,
        update_interval=timedelta(seconds=update_interval_sec),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_refresh(call: ServiceCall) -> None:
        """Handle manual data refresh service call."""
        _LOGGER.info("Manual refresh triggered for WooCommerce store(s)")
        for coord in hass.data.get(DOMAIN, {}).values():
            if isinstance(coord, WooCommerceDataUpdateCoordinator):
                await coord.async_request_refresh()

    async def handle_get_order(call: ServiceCall) -> ServiceResponse:
        """Handle on-demand query for an order by ID."""
        order_id = call.data[ATTR_ORDER_ID]
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if not coordinators:
            return {"error": "No WooCommerce store configured"}
        coord = coordinators[0]
        try:
            return await coord.client.get_order(order_id)
        except WooCommerceApiError as err:
            return {"error": str(err)}

    async def handle_get_product(call: ServiceCall) -> ServiceResponse:
        """Handle on-demand query for a product by ID."""
        product_id = call.data[ATTR_PRODUCT_ID]
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if not coordinators:
            return {"error": "No WooCommerce store configured"}
        coord = coordinators[0]
        try:
            return await coord.client.get_product(product_id)
        except WooCommerceApiError as err:
            return {"error": str(err)}

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)

    if not hass.services.has_service(DOMAIN, SERVICE_GET_ORDER):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_ORDER,
            handle_get_order,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GET_PRODUCT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_PRODUCT,
            handle_get_product,
            supports_response=SupportsResponse.ONLY,
        )

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for srv in (SERVICE_REFRESH, SERVICE_GET_ORDER, SERVICE_GET_PRODUCT):
                if hass.services.has_service(DOMAIN, srv):
                    hass.services.async_remove(DOMAIN, srv)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
