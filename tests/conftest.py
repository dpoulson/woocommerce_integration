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
        m = MagicMock()
        m.__path__ = []
        sys.modules[mod] = m

sys.modules["homeassistant"].config_entries = sys.modules["homeassistant.config_entries"]
sys.modules["homeassistant"].core = sys.modules["homeassistant.core"]
sys.modules["homeassistant"].data_entry_flow = sys.modules["homeassistant.data_entry_flow"]
sys.modules["homeassistant"].helpers = sys.modules["homeassistant.helpers"]
sys.modules["homeassistant"].components = sys.modules["homeassistant.components"]
sys.modules["homeassistant.core"].callback = lambda f: f


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


class MockOptionsFlow:
    """Mock base OptionsFlow with read-only config_entry property (as in HA 2025+)."""

    _config_entry: Any = None

    @property
    def config_entry(self) -> Any:
        return self._config_entry

    def async_show_form(self, step_id: str, data_schema: Any, errors: Any = None) -> dict[str, Any]:
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}

    def async_create_entry(self, title: str = "", data: Any = None) -> dict[str, Any]:
        return {"type": "create_entry", "title": title, "data": data}


class MockConfigFlow:
    """Mock base ConfigFlow."""

    def __init_subclass__(cls, domain: str | None = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.domain = domain

    def async_show_form(self, step_id: str, data_schema: Any, errors: Any = None) -> dict[str, Any]:
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}

    def async_create_entry(self, title: str, data: Any) -> dict[str, Any]:
        return {"type": "create_entry", "title": title, "data": data}


sys.modules["homeassistant.config_entries"].OptionsFlow = MockOptionsFlow
sys.modules["homeassistant.config_entries"].ConfigFlow = MockConfigFlow
sys.modules["homeassistant.components.sensor"].SensorStateClass = SensorStateClass
sys.modules["homeassistant.components.sensor"].SensorEntityDescription = SensorEntityDescription
sys.modules["homeassistant.components.sensor"].SensorEntity = SensorEntity
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = DeviceInfo

