"""Unit tests for WooCommerceApiClient."""
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.woocommerce_store.api import (
    WooCommerceApiClient,
    WooCommerceAuthError,
    WooCommerceConnectionError,
)


@pytest.mark.asyncio
async def test_url_formatting():
    """Test URL normalization."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("example.com/", "ck_123", "cs_456", session)
    assert client.base_url == "https://example.com"
    assert client._get_url("orders") == "https://example.com/wp-json/wc/v3/orders"


@pytest.mark.asyncio
async def test_get_orders_totals():
    """Test get_orders_totals parses API response."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://example.com", "ck_123", "cs_456", session)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value=[
            {"slug": "pending", "total": "2"},
            {"slug": "processing", "total": 5},
            {"slug": "completed", "total": "12"},
        ]
    )

    session.get.return_value.__aenter__.return_value = mock_response

    totals = await client.get_orders_totals()
    assert totals == {"pending": 2, "processing": 5, "completed": 12}


@pytest.mark.asyncio
async def test_get_products_totals():
    """Test get_products_totals sums product types and retrieves stock stats."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://example.com", "ck_123", "cs_456", session)

    # Mock client._request for different endpoints
    async def mock_request(endpoint: str, params=None, namespace="wc/v3"):
        if endpoint == "reports/products/totals":
            return [
                {"slug": "simple", "name": "Simple product", "total": 35},
                {"slug": "variable", "name": "Variable product", "total": 10},
            ]
        if endpoint == "reports/stock/stats" and namespace == "wc-analytics":
            return {
                "totals": {
                    "products_low_stock": 3,
                    "products_out_of_stock": 2,
                }
            }
        return {}

    client._request = AsyncMock(side_effect=mock_request)

    totals = await client.get_products_totals()
    assert totals["total"] == 45
    assert totals["simple"] == 35
    assert totals["variable"] == 10
    assert totals["lowstock"] == 3
    assert totals["outofstock"] == 2
    assert totals["instock"] == 43


@pytest.mark.asyncio
async def test_get_recent_orders():
    """Test get_recent_orders parses and structures order details."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://example.com", "ck_123", "cs_456", session)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value=[
            {
                "id": 1001,
                "number": "1001",
                "status": "processing",
                "total": "49.99",
                "currency": "GBP",
                "date_created": "2026-09-14T12:00:00",
                "billing": {"first_name": "John", "last_name": "Doe"},
                "payment_method_title": "Credit Card",
                "line_items": [
                    {"name": "Widget A", "quantity": 2, "total": "30.00"},
                    {"name": "Widget B", "quantity": 1, "total": "19.99"},
                ],
            }
        ]
    )

    session.get.return_value.__aenter__.return_value = mock_response

    orders = await client.get_recent_orders(limit=1)
    assert len(orders) == 1
    assert orders[0]["customer_name"] == "John Doe"
    assert orders[0]["item_count"] == 3
    assert orders[0]["total"] == "49.99"


@pytest.mark.asyncio
async def test_auth_error_handling():
    """Test 401 raises WooCommerceAuthError."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://example.com", "ck_bad", "cs_bad", session)

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")
    session.get.return_value.__aenter__.return_value = mock_response

    with pytest.raises(WooCommerceAuthError):
        await client.test_connection()


@pytest.mark.asyncio
async def test_connection_error_handling():
    """Test connector error raises WooCommerceConnectionError."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://invalid-host", "ck_1", "cs_1", session)

    session.get.return_value.__aenter__.side_effect = aiohttp.ClientConnectorError(
        connection_key=MagicMock(), os_error=OSError("Host unreachable")
    )

    with pytest.raises(WooCommerceConnectionError):
        await client.test_connection()


@pytest.mark.asyncio
async def test_fetch_all_data():
    """Test parallel fetch of all data sets."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = WooCommerceApiClient("https://example.com", "ck_1", "cs_1", session)

    client.get_orders_totals = AsyncMock(return_value={"processing": 3, "completed": 10})
    client.get_products_totals = AsyncMock(return_value={"total": 20})
    client.get_recent_orders = AsyncMock(return_value=[{"id": 1, "number": "1"}])
    client.get_sales_report = AsyncMock(return_value={"total_sales": "150.00"})

    data = await client.fetch_all_data()
    assert data.orders_totals == {"processing": 3, "completed": 10}
    assert data.products_totals == {"total": 20}
    assert len(data.recent_orders) == 1
    assert data.sales_today == {"total_sales": "150.00"}
