"""Sensor platform for WooCommerce Store integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WooCommerceData
from .const import DOMAIN
from .coordinator import WooCommerceDataUpdateCoordinator


@dataclass(frozen=True)
class WooCommerceSensorEntityDescription(SensorEntityDescription):
    """Class describing WooCommerce sensor entities."""

    value_fn: Callable[[WooCommerceData], Any] = lambda _: None
    attrs_fn: Callable[[WooCommerceData], dict[str, Any]] | None = None


ORDER_STATUS_SENSORS: tuple[WooCommerceSensorEntityDescription, ...] = (
    WooCommerceSensorEntityDescription(
        key="total_orders",
        name="Total Orders",
        icon="mdi:cart",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="orders",
        value_fn=lambda data: sum(data.orders_totals.values()),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_processing",
        name="Orders Processing",
        icon="mdi:progress-clock",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("processing", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_pending",
        name="Orders Pending",
        icon="mdi:clock-alert-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("pending", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_completed",
        name="Orders Completed",
        icon="mdi:check-circle-outline",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("completed", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_on_hold",
        name="Orders On Hold",
        icon="mdi:pause-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("on-hold", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_cancelled",
        name="Orders Cancelled",
        icon="mdi:close-circle-outline",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("cancelled", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_refunded",
        name="Orders Refunded",
        icon="mdi:cash-refund",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("refunded", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="orders_failed",
        name="Orders Failed",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="orders",
        value_fn=lambda data: data.orders_totals.get("failed", 0),
    ),
)

PRODUCT_SENSORS: tuple[WooCommerceSensorEntityDescription, ...] = (
    WooCommerceSensorEntityDescription(
        key="total_products",
        name="Total Products",
        icon="mdi:package-variant-closed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="products",
        value_fn=lambda data: data.products_totals.get("total", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="products_instock",
        name="Products In Stock",
        icon="mdi:package-variant-closed-check",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="products",
        value_fn=lambda data: data.products_totals.get("instock", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="products_lowstock",
        name="Products Low Stock",
        icon="mdi:package-variant-closed-alert",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="products",
        value_fn=lambda data: data.products_totals.get("lowstock", 0),
    ),
    WooCommerceSensorEntityDescription(
        key="products_outofstock",
        name="Products Out of Stock",
        icon="mdi:package-variant-closed-remove",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="products",
        value_fn=lambda data: data.products_totals.get("outofstock", 0),
    ),
)


def _extract_latest_order_attrs(data: WooCommerceData) -> dict[str, Any]:
    """Extract attributes for latest order sensor."""
    if not data.recent_orders:
        return {"recent_orders": []}
    latest = data.recent_orders[0]
    return {
        "order_id": latest.get("id"),
        "number": latest.get("number"),
        "customer_name": latest.get("customer_name"),
        "status": latest.get("status"),
        "total": latest.get("total"),
        "currency": latest.get("currency"),
        "date_created": latest.get("date_created"),
        "item_count": latest.get("item_count"),
        "line_items": latest.get("line_items"),
        "recent_orders": data.recent_orders,
    }


LATEST_ORDER_SENSOR = WooCommerceSensorEntityDescription(
    key="latest_order",
    name="Latest Order",
    icon="mdi:receipt",
    value_fn=lambda data: (
        f"#{data.recent_orders[0]['number']}" if data.recent_orders else "None"
    ),
    attrs_fn=_extract_latest_order_attrs,
)

SALES_TODAY_SENSOR = WooCommerceSensorEntityDescription(
    key="sales_today",
    name="Sales Today",
    icon="mdi:cash-multiple",
    state_class=SensorStateClass.TOTAL,
    value_fn=lambda data: (
        float(data.sales_today.get("total_sales", 0.0))
        if data.sales_today and "total_sales" in data.sales_today
        else 0.0
    ),
    attrs_fn=lambda data: (
        {
            "total_orders": data.sales_today.get("total_orders", 0),
            "total_items": data.sales_today.get("total_items", 0),
            "total_tax": data.sales_today.get("total_tax", "0.00"),
            "total_shipping": data.sales_today.get("total_shipping", "0.00"),
            "total_discount": data.sales_today.get("total_discount", "0.00"),
        }
        if data.sales_today
        else {}
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WooCommerce sensor entities based on a config entry."""
    coordinator: WooCommerceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    descriptions: list[WooCommerceSensorEntityDescription] = [
        *ORDER_STATUS_SENSORS,
        *PRODUCT_SENSORS,
        LATEST_ORDER_SENSOR,
        SALES_TODAY_SENSOR,
    ]

    entities = [
        WooCommerceSensor(coordinator, entry, description)
        for description in descriptions
    ]

    async_add_entities(entities)


class WooCommerceSensor(CoordinatorEntity[WooCommerceDataUpdateCoordinator], SensorEntity):
    """Representation of a WooCommerce sensor."""

    entity_description: WooCommerceSensorEntityDescription

    def __init__(
        self,
        coordinator: WooCommerceDataUpdateCoordinator,
        entry: ConfigEntry,
        description: WooCommerceSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="WooCommerce",
            model="REST API v3",
            configuration_url=coordinator.client.base_url,
        )

    @property
    def native_value(self) -> Any:
        """Return native value from coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if self.coordinator.data is None or not self.entity_description.attrs_fn:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
