"""Test component setup."""

from homeassistant.setup import async_setup_component
from homeassistant.core import HomeAssistant

from custom_components.kitchenowl.const import DOMAIN


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True
