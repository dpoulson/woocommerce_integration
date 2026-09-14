"""Pytest configuration and Home Assistant module mocks."""
import sys
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
