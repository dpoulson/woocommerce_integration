"""Pytest configuration and Home Assistant module mocks."""
from dataclasses import dataclass
from enum import StrEnum
import sys
from typing import Any
from unittest.mock import MagicMock

# Mock homeassistant modules if not installed in current environment
ha_modules = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.components",
    "homeassistant.components.sensor",
]

for mod in ha_modules:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()


class SensorStateClass(StrEnum):
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


@dataclass(frozen=True)
class SensorEntityDescription:
    key: str = ""
    name: str | None = None
    icon: str | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement: str | None = None


class SensorEntity:
    """Mock SensorEntity."""

    entity_description: SensorEntityDescription
    _attr_has_entity_name: bool = False
    _attr_unique_id: str | None = None
    _attr_device_info: Any = None
    _attr_suggested_object_id: str | None = None


class CoordinatorEntity:
    """Mock CoordinatorEntity."""

    def __init__(self, coordinator: Any) -> None:
        self.coordinator = coordinator

    def __class_getitem__(cls, item: Any) -> type:
        return cls


@dataclass
class DeviceInfo:
    identifiers: set[tuple[str, str]]
    name: str
    manufacturer: str
    model: str
    configuration_url: str


sys.modules["homeassistant.components.sensor"].SensorStateClass = SensorStateClass
sys.modules["homeassistant.components.sensor"].SensorEntityDescription = SensorEntityDescription
sys.modules["homeassistant.components.sensor"].SensorEntity = SensorEntity
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = DeviceInfo

