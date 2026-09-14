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
    products_totals: dict[str, Any]
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

    def _get_url(self, endpoint: str, namespace: str = "wc/v3") -> str:
        """Construct endpoint URL."""
        endpoint = endpoint.lstrip("/")
        return f"{self._base_url}/wp-json/{namespace}/{endpoint}"

    def _prepare_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        namespace: str = "wc/v3",
    ) -> tuple[str, dict[str, Any], dict[str, str]]:
        """Prepare URL, params, and headers."""
        url = self._get_url(endpoint, namespace=namespace)
        request_params = dict(params) if params else {}
        headers: dict[str, str] = {}

        if self._is_https:
            credentials = f"{self._consumer_key}:{self._consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode("ascii")
            headers["Authorization"] = f"Basic {encoded}"
        else:
            request_params["consumer_key"] = self._consumer_key
            request_params["consumer_secret"] = self._consumer_secret

        return url, request_params, headers

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        namespace: str = "wc/v3",
    ) -> Any:
        """Execute an asynchronous HTTP GET request."""
        url, request_params, headers = self._prepare_request(
            endpoint, params=params, namespace=namespace
        )

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

    async def _get_headers(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        namespace: str = "wc/v3",
    ) -> dict[str, str]:
        """Execute request and return lowercased response headers."""
        url, request_params, headers = self._prepare_request(
            endpoint, params=params, namespace=namespace
        )

        try:
            async with self._session.get(
                url,
                params=request_params,
                headers=headers,
                ssl=self._verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as response:
                if response.status in (401, 403):
                    raise WooCommerceAuthError(f"Authentication failed ({response.status})")
                if response.status >= 400:
                    raise WooCommerceApiError(f"API request failed with HTTP status {response.status}")
                return {k.lower(): v for k, v in response.headers.items()}
        except (aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as err:
            raise WooCommerceConnectionError(f"Connection to WooCommerce failed: {err}") from err

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

    async def get_products_totals(self) -> dict[str, Any]:
        """Fetch product count metrics."""
        totals: dict[str, Any] = {
            "total": 0,
            "instock": 0,
            "lowstock": 0,
            "outofstock": 0,
            "lowstock_items": [],
            "outofstock_items": [],
        }

        # 1. Fetch products totals by type (simple, variable, etc.) and calculate total count
        try:
            data = await self._request("reports/products/totals")
            if isinstance(data, list):
                type_sum = 0
                for item in data:
                    slug = item.get("slug")
                    count = int(item.get("total", 0))
                    if slug:
                        totals[slug] = count
                    type_sum += count
                totals["total"] = type_sum
        except WooCommerceApiError as err:
            _LOGGER.debug("Could not fetch reports/products/totals: %s", err)

        # 2. If total is still 0, try X-WP-Total header from /wc/v3/products
        if totals["total"] == 0:
            try:
                headers = await self._get_headers("products", params={"per_page": 1})
                if "x-wp-total" in headers:
                    totals["total"] = int(headers["x-wp-total"])
            except WooCommerceApiError as err:
                _LOGGER.debug("Could not fetch products total via header: %s", err)

        # 3. Calculate stock metrics directly from product items
        try:
            pages_to_fetch = min(5, (totals["total"] + 99) // 100) if totals["total"] > 0 else 1
            tasks = [
                self._request(
                    "products",
                    params={
                        "per_page": 100,
                        "page": page,
                        "status": "publish",
                        "_fields": "id,name,price,manage_stock,stock_quantity,stock_status,low_stock_amount",
                    },
                )
                for page in range(1, pages_to_fetch + 1)
            ]
            pages_results = await asyncio.gather(*tasks, return_exceptions=True)

            instock = 0
            lowstock = 0
            outofstock = 0
            lowstock_items: list[dict[str, Any]] = []
            outofstock_items: list[dict[str, Any]] = []
            found_any = False

            for res in pages_results:
                if isinstance(res, list):
                    found_any = True
                    for p in res:
                        status = p.get("stock_status")
                        qty = p.get("stock_quantity")
                        managed = p.get("manage_stock", False)
                        raw_thresh = p.get("low_stock_amount")
                        thresh = int(raw_thresh) if raw_thresh is not None else 2
                        item_summary = {
                            "id": p.get("id"),
                            "name": p.get("name"),
                            "price": p.get("price"),
                            "stock_quantity": qty,
                        }

                        if status == "outofstock" or (managed and qty is not None and qty <= 0):
                            outofstock += 1
                            outofstock_items.append(item_summary)
                        elif managed and qty is not None and 0 < qty <= thresh:
                            lowstock += 1
                            lowstock_items.append(item_summary)
                        elif status == "instock" or (managed and qty is not None and qty > thresh):
                            instock += 1

            if found_any:
                totals["instock"] = instock
                totals["lowstock"] = lowstock
                totals["outofstock"] = outofstock
                totals["lowstock_items"] = lowstock_items
                totals["outofstock_items"] = outofstock_items
                _LOGGER.debug(
                    "Products stock calculated: total=%d, in=%d, low=%d, out=%d",
                    totals["total"],
                    instock,
                    lowstock,
                    outofstock,
                )
                return totals
        except WooCommerceApiError as err:
            _LOGGER.debug("Could not calculate stock from products list: %s", err)

        # 4. Fallback: Query X-WP-Total for stock statuses
        try:
            headers_out = await self._get_headers(
                "products", params={"per_page": 1, "stock_status": "outofstock"}
            )
            if "x-wp-total" in headers_out:
                totals["outofstock"] = int(headers_out["x-wp-total"])

            headers_in = await self._get_headers(
                "products", params={"per_page": 1, "stock_status": "instock"}
            )
            if "x-wp-total" in headers_in:
                totals["instock"] = int(headers_in["x-wp-total"])
            else:
                totals["instock"] = max(0, totals["total"] - totals["outofstock"])
        except WooCommerceApiError as err:
            _LOGGER.debug("Could not fetch stock totals via headers: %s", err)
            totals["instock"] = totals["total"]

        return totals

    async def get_order(self, order_id: int | str) -> dict[str, Any]:
        """Fetch details of a specific order."""
        data = await self._request(f"orders/{order_id}")
        if not isinstance(data, dict):
            raise WooCommerceApiError(f"Unexpected response fetching order {order_id}")
        return data

    async def get_product(self, product_id: int | str) -> dict[str, Any]:
        """Fetch details of a specific product."""
        data = await self._request(f"products/{product_id}")
        if not isinstance(data, dict):
            raise WooCommerceApiError(f"Unexpected response fetching product {product_id}")
        return data

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
