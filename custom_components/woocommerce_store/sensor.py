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


def _extract_orders_processing_attrs(data: WooCommerceData) -> dict[str, Any]:
    """Extract attributes for processing orders sensor."""
    return {
        "pending_units_by_product": {
            pid: {
                "name": data.products_sales.get(pid, {}).get("name", f"Product {pid}"),
                "quantity": qty,
            }
            for pid, qty in data.pending_units_by_product.items()
        }
    }


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
        attrs_fn=_extract_orders_processing_attrs,
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
        attrs_fn=lambda data: {
            f"type_{k}": v
            for k, v in data.products_totals.items()
            if k not in ("total", "instock", "lowstock", "outofstock")
        },
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
        attrs_fn=lambda data: {
            "items": data.products_totals.get("lowstock_items", [])
        },
    ),
    WooCommerceSensorEntityDescription(
        key="products_outofstock",
        name="Products Out of Stock",
        icon="mdi:package-variant-closed-remove",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="products",
        value_fn=lambda data: data.products_totals.get("outofstock", 0),
        attrs_fn=lambda data: {
            "items": data.products_totals.get("outofstock_items", [])
        },
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

    entities: list[SensorEntity] = [
        WooCommerceSensor(coordinator, entry, description)
        for description in descriptions
    ]

    known_product_ids: set[int] = set()

    if coordinator.data and coordinator.data.products_sales:
        for pid in coordinator.data.products_sales:
            known_product_ids.add(pid)
            entities.append(
                WooCommerceProductSensor(coordinator, entry, pid, "pending_units")
            )
            entities.append(
                WooCommerceProductSensor(coordinator, entry, pid, "total_sales")
            )

    async_add_entities(entities)

    def _add_new_product_entities() -> None:
        if not coordinator.data or not coordinator.data.products_sales:
            return
        new_entities: list[SensorEntity] = []
        for pid in coordinator.data.products_sales:
            if pid not in known_product_ids:
                known_product_ids.add(pid)
                new_entities.append(
                    WooCommerceProductSensor(coordinator, entry, pid, "pending_units")
                )
                new_entities.append(
                    WooCommerceProductSensor(coordinator, entry, pid, "total_sales")
                )
        if new_entities:
            async_add_entities(new_entities)

    if hasattr(entry, "async_on_unload"):
        entry.async_on_unload(coordinator.async_add_listener(_add_new_product_entities))
    else:
        coordinator.async_add_listener(_add_new_product_entities)


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


class WooCommerceProductSensor(
    CoordinatorEntity[WooCommerceDataUpdateCoordinator], SensorEntity
):
    """Representation of a per-product WooCommerce sensor."""

    def __init__(
        self,
        coordinator: WooCommerceDataUpdateCoordinator,
        entry: ConfigEntry,
        product_id: int,
        sensor_type: str,
    ) -> None:
        """Initialize the product sensor."""
        super().__init__(coordinator)
        self.product_id = product_id
        self.sensor_type = sensor_type

        product = (
            coordinator.data.products_sales.get(product_id, {})
            if coordinator.data
            else {}
        )
        product_name = product.get("name") or f"Product {product_id}"
        product_slug = product.get("slug") or f"product_{product_id}"
        safe_slug = product_slug.replace("-", "_").lower()

        if sensor_type == "pending_units":
            self.entity_description = SensorEntityDescription(
                key=f"{safe_slug}_pending_units",
                name=f"{product_name} Pending Units",
                icon="mdi:clipboard-clock",
                native_unit_of_measurement="units",
                state_class=SensorStateClass.MEASUREMENT,
            )
            self._attr_unique_id = f"{entry.entry_id}_{product_id}_pending_units"
        else:
            self.entity_description = SensorEntityDescription(
                key=f"{safe_slug}_total_sales",
                name=f"{product_name} Total Sales",
                icon="mdi:chart-line",
                native_unit_of_measurement="units",
                state_class=SensorStateClass.TOTAL,
            )
            self._attr_unique_id = f"{entry.entry_id}_{product_id}_total_sales"

        self._attr_suggested_object_id = f"{safe_slug}_{sensor_type}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="WooCommerce",
            model="REST API v3",
            configuration_url=coordinator.client.base_url,
        )

    @property
    def native_value(self) -> int | None:
        """Return native value from coordinator data."""
        if not self.coordinator.data:
            return None
        if self.sensor_type == "pending_units":
            return self.coordinator.data.pending_units_by_product.get(
                self.product_id, 0
            )
        product = self.coordinator.data.products_sales.get(self.product_id, {})
        return product.get("total_sales", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return None
        product = self.coordinator.data.products_sales.get(self.product_id, {})
        attrs: dict[str, Any] = {
            "product_id": self.product_id,
            "product_name": product.get("name"),
            "slug": product.get("slug"),
            "stock_quantity": product.get("stock_quantity"),
        }
        if self.sensor_type == "total_sales":
            attrs["price"] = product.get("price")
        return attrs
