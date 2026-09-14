"""DataUpdateCoordinator for WooCommerce Store integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WooCommerceApiClient, WooCommerceApiError, WooCommerceData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WooCommerceDataUpdateCoordinator(DataUpdateCoordinator[WooCommerceData]):
    """Class to manage fetching WooCommerce data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WooCommerceApiClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> WooCommerceData:
        """Fetch data from WooCommerce."""
        try:
            return await self.client.fetch_all_data()
        except WooCommerceApiError as err:
            raise UpdateFailed(f"Error communicating with WooCommerce API: {err}") from err
