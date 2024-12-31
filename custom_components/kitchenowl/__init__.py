"""KitchenOwl integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from kitchenowl_python.exceptions import KitchenOwlAuthException, KitchenOwlException
from kitchenowl_python.kitchenowl import KitchenOwl

from .const import CONF_HOUSEHOLD, DOMAIN
from .coordinator import KitchenOwlDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.TODO]

_LOGGER = logging.getLogger(__name__)

type KitchenOwlConfigEntry = ConfigEntry[KitchenOwlDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, config: KitchenOwlConfigEntry) -> bool:
    """Set up the Kitchenowl component from config entry."""
    host = config.data[CONF_HOST]
    token = config.data[CONF_ACCESS_TOKEN]
    verify_ssl = config.data.get(CONF_VERIFY_SSL, True)
    session = async_get_clientsession(hass, verify_ssl=verify_ssl)

    kitchenowl = KitchenOwl(session, host, token)
    try:
        await kitchenowl.test_connection()
        households = await kitchenowl.get_households()
        if not households:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="no_households_found_exception",
            )
        if config.data[CONF_HOUSEHOLD] is None or config.data[CONF_HOUSEHOLD] not in (
            str(h["id"]) for h in households
        ):
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="household_not_in_households_list_exception",
                translation_placeholders={
                    "household": config.data[CONF_HOUSEHOLD],
                },
            )

    except KitchenOwlAuthException as e:
        raise ConfigEntryAuthFailed from e
    except TimeoutError as e:
        raise ConfigEntryNotReady from e
    except KitchenOwlException as e:
        raise ConfigEntryNotReady from e

    coordinator = KitchenOwlDataUpdateCoordinator(
        hass, kitchenowl, config.data[CONF_HOUSEHOLD]
    )
    await coordinator.async_config_entry_first_refresh()

    config.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
