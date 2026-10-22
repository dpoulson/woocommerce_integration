"""Unit tests for WooCommerce config and options flows."""
from unittest.mock import MagicMock
import pytest

from custom_components.woocommerce_store.config_flow import (
    WooCommerceConfigFlow,
    WooCommerceOptionsFlowHandler,
)
from custom_components.woocommerce_store.const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_UPDATE_INTERVAL: 300,
    }
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_options_flow_init_with_read_only_property(mock_config_entry):
    """Test options flow does not crash when config_entry is read-only property."""
    # Instantiation via async_get_options_flow
    flow = WooCommerceConfigFlow.async_get_options_flow(mock_config_entry)
    assert isinstance(flow, WooCommerceOptionsFlowHandler)
    assert flow.config_entry == mock_config_entry

    # Show form step
    result = await flow.async_step_init()
    assert result["type"] == "form"
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_submission(mock_config_entry):
    """Test options flow saves updated interval."""
    flow = WooCommerceOptionsFlowHandler(mock_config_entry)

    result = await flow.async_step_init(user_input={CONF_UPDATE_INTERVAL: 600})
    assert result["type"] == "create_entry"
    assert result["data"] == {CONF_UPDATE_INTERVAL: 600}


@pytest.mark.asyncio
async def test_options_flow_ha_injected_entry(mock_config_entry):
    """Test options flow when Home Assistant injects entry without constructor argument."""
    flow = WooCommerceOptionsFlowHandler()
    flow._config_entry = mock_config_entry

    assert flow.config_entry == mock_config_entry
    result = await flow.async_step_init()
    assert result["type"] == "form"
