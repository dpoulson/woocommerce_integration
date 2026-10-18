"""Unit tests for WooCommerce Store sensors."""
from unittest.mock import MagicMock
import pytest

from custom_components.woocommerce_store.api import WooCommerceData
from custom_components.woocommerce_store.const import DOMAIN
from custom_components.woocommerce_store.sensor import (
    ORDER_STATUS_SENSORS,
    WooCommerceProductSensor,
    WooCommerceSensor,
    async_setup_entry,
)
from tests.conftest import SensorStateClass


@pytest.fixture
def sample_data():
    """Sample WooCommerceData fixture."""
    return WooCommerceData(
        orders_totals={"processing": 3, "pending": 1, "completed": 10},
        products_totals={"total": 2, "instock": 2},
        recent_orders=[],
        sales_today={"total_sales": "100.00"},
        products_sales={
            180: {
                "id": 180,
                "name": "Astropixels Kit",
                "slug": "astropixels-kit",
                "total_sales": 25,
                "stock_quantity": 8,
                "price": "89.99",
            },
            190: {
                "id": 190,
                "name": "Power Module",
                "slug": "power-module",
                "total_sales": 5,
                "stock_quantity": 2,
                "price": "24.50",
            },
        },
        pending_units_by_product={
            180: 4,
            190: 1,
        },
    )


def test_orders_processing_attributes(sample_data):
    """Test orders_processing sensor attributes include pending_units_by_product."""
    proc_desc = next(d for d in ORDER_STATUS_SENSORS if d.key == "orders_processing")
    assert proc_desc.attrs_fn is not None

    attrs = proc_desc.attrs_fn(sample_data)
    assert "pending_units_by_product" in attrs
    mapping = attrs["pending_units_by_product"]
    assert mapping[180] == {"name": "Astropixels Kit", "quantity": 4}
    assert mapping[190] == {"name": "Power Module", "quantity": 1}


def test_woocommerce_product_sensor_pending_units(sample_data):
    """Test product pending units sensor configuration and values."""
    coordinator = MagicMock()
    coordinator.data = sample_data
    coordinator.client.base_url = "https://example.com"

    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.title = "Astropixels Store"

    sensor = WooCommerceProductSensor(coordinator, entry, 180, "pending_units")

    assert sensor.entity_description.key == "astropixels_kit_pending_units"
    assert sensor.entity_description.name == "Astropixels Kit Pending Units"
    assert sensor.entity_description.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_description.native_unit_of_measurement == "units"
    assert sensor._attr_unique_id == "test_entry_123_180_pending_units"
    assert sensor._attr_suggested_object_id == "astropixels_kit_pending_units"
    assert sensor._attr_device_info.identifiers == {(DOMAIN, "test_entry_123")}

    assert sensor.native_value == 4
    attrs = sensor.extra_state_attributes
    assert attrs["product_id"] == 180
    assert attrs["product_name"] == "Astropixels Kit"
    assert attrs["slug"] == "astropixels-kit"
    assert attrs["stock_quantity"] == 8


def test_woocommerce_product_sensor_total_sales(sample_data):
    """Test product total sales sensor configuration and values."""
    coordinator = MagicMock()
    coordinator.data = sample_data
    coordinator.client.base_url = "https://example.com"

    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.title = "Astropixels Store"

    sensor = WooCommerceProductSensor(coordinator, entry, 180, "total_sales")

    assert sensor.entity_description.key == "astropixels_kit_total_sales"
    assert sensor.entity_description.name == "Astropixels Kit Total Sales"
    assert sensor.entity_description.state_class == SensorStateClass.TOTAL
    assert sensor.entity_description.native_unit_of_measurement == "units"
    assert sensor._attr_unique_id == "test_entry_123_180_total_sales"
    assert sensor._attr_suggested_object_id == "astropixels_kit_total_sales"

    assert sensor.native_value == 25
    attrs = sensor.extra_state_attributes
    assert attrs["product_id"] == 180
    assert attrs["product_name"] == "Astropixels Kit"
    assert attrs["slug"] == "astropixels-kit"
    assert attrs["stock_quantity"] == 8
    assert attrs["price"] == "89.99"


@pytest.mark.asyncio
async def test_async_setup_entry_creates_product_sensors(sample_data):
    """Test async_setup_entry creates both standard and per-product sensors."""
    hass = MagicMock()
    coordinator = MagicMock()
    coordinator.data = sample_data
    coordinator.client.base_url = "https://example.com"

    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.title = "Astropixels Store"
    hass.data = {DOMAIN: {entry.entry_id: coordinator}}

    added_entities = []

    def mock_add_entities(new_entities):
        added_entities.extend(new_entities)

    await async_setup_entry(hass, entry, mock_add_entities)

    product_sensors = [e for e in added_entities if isinstance(e, WooCommerceProductSensor)]
    assert len(product_sensors) == 4  # 2 products * 2 sensors each

    keys = {s.entity_description.key for s in product_sensors}
    assert "astropixels_kit_pending_units" in keys
    assert "astropixels_kit_total_sales" in keys
    assert "power_module_pending_units" in keys
    assert "power_module_total_sales" in keys
