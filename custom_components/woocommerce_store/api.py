"""Asynchronous API client for WooCommerce REST API."""
from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WooCommerceApiError(Exception):
    """Base exception for WooCommerce API errors."""


class WooCommerceAuthError(WooCommerceApiError):
    """Authentication or permission error."""


class WooCommerceConnectionError(WooCommerceApiError):
    """Network connection or timeout error."""


@dataclass
class WooCommerceData:
    """Consolidated store data."""

    orders_totals: dict[str, int]
    products_totals: dict[str, int]
    recent_orders: list[dict[str, Any]]
    sales_today: dict[str, Any] | None = None


class WooCommerceApiClient:
    """Client to communicate with WooCommerce REST API."""

    def __init__(
        self,
        url: str,
        consumer_key: str,
        consumer_secret: str,
        session: aiohttp.ClientSession,
        verify_ssl: bool = True,
        timeout: int = 15,
    ) -> None:
        """Initialize the API client."""
        clean_url = url.strip().rstrip("/")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        self._base_url = clean_url
        self._consumer_key = consumer_key.strip()
        self._consumer_secret = consumer_secret.strip()
        self._session = session
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._is_https = clean_url.startswith("https://")

    @property
    def base_url(self) -> str:
        """Return base URL."""
        return self._base_url

    def _get_url(self, endpoint: str) -> str:
        """Construct endpoint URL."""
        endpoint = endpoint.lstrip("/")
        return f"{self._base_url}/wp-json/wc/v3/{endpoint}"

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an asynchronous HTTP GET request."""
        url = self._get_url(endpoint)
        request_params = dict(params) if params else {}

        headers: dict[str, str] = {}
        if self._is_https:
            credentials = f"{self._consumer_key}:{self._consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode("ascii")
            headers["Authorization"] = f"Basic {encoded}"
        else:
            request_params["consumer_key"] = self._consumer_key
            request_params["consumer_secret"] = self._consumer_secret

        try:
            async with self._session.get(
                url,
                params=request_params,
                headers=headers,
                ssl=self._verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as response:
                if response.status in (401, 403):
                    raise WooCommerceAuthError(
                        f"Authentication failed ({response.status}): {await response.text()}"
                    )
                if response.status >= 400:
                    raise WooCommerceApiError(
                        f"API request failed with HTTP status {response.status}: {await response.text()}"
                    )
                return await response.json()
        except (aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as err:
            raise WooCommerceConnectionError(f"Connection to WooCommerce failed: {err}") from err
        except (WooCommerceAuthError, WooCommerceApiError):
            raise
        except Exception as err:
            raise WooCommerceApiError(f"Unexpected error communicating with WooCommerce: {err}") from err

    async def test_connection(self) -> bool:
        """Test API connection and credentials."""
        # Use reports/orders/totals or system_status to verify read permissions
        data = await self._request("reports/orders/totals")
        return isinstance(data, list)

    async def get_orders_totals(self) -> dict[str, int]:
        """Fetch total order counts grouped by status."""
        data = await self._request("reports/orders/totals")
        totals: dict[str, int] = {}
        if isinstance(data, list):
            for item in data:
                slug = item.get("slug")
                total = item.get("total", 0)
                if slug:
                    totals[slug] = int(total)
        return totals

    async def get_products_totals(self) -> dict[str, int]:
        """Fetch product count metrics."""
        data = await self._request("reports/products/totals")
        totals: dict[str, int] = {}
        if isinstance(data, list):
            for item in data:
                slug = item.get("slug")
                total = item.get("total", 0)
                if slug:
                    totals[slug] = int(total)
        return totals

    async def get_recent_orders(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch recent orders with details."""
        data = await self._request(
            "orders",
            params={"per_page": limit, "orderby": "date", "order": "desc"},
        )
        if not isinstance(data, list):
            return []

        cleaned_orders = []
        for order in data:
            billing = order.get("billing", {})
            customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            line_items = [
                {
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "total": item.get("total"),
                }
                for item in order.get("line_items", [])
            ]
            cleaned_orders.append(
                {
                    "id": order.get("id"),
                    "number": order.get("number"),
                    "status": order.get("status"),
                    "total": order.get("total"),
                    "currency": order.get("currency"),
                    "date_created": order.get("date_created"),
                    "customer_name": customer_name or "Guest",
                    "payment_method_title": order.get("payment_method_title"),
                    "line_items": line_items,
                    "item_count": sum(item.get("quantity", 0) for item in line_items),
                }
            )
        return cleaned_orders

    async def get_sales_report(self, period: str = "today") -> dict[str, Any] | None:
        """Fetch sales report for a given period."""
        try:
            data = await self._request("reports/sales", params={"period": period})
            if isinstance(data, list) and data:
                return data[0]
        except WooCommerceApiError as err:
            _LOGGER.debug("Could not fetch sales report: %s", err)
        return None

    async def fetch_all_data(self) -> WooCommerceData:
        """Fetch all store data in parallel."""
        orders_totals, products_totals, recent_orders, sales_today = await asyncio.gather(
            self.get_orders_totals(),
            self.get_products_totals(),
            self.get_recent_orders(limit=5),
            self.get_sales_report(period="today"),
            return_exceptions=False,
        )
        return WooCommerceData(
            orders_totals=orders_totals,
            products_totals=products_totals,
            recent_orders=recent_orders,
            sales_today=sales_today,
        )
