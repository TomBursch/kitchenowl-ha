"""Config Flow for the KitchenOwl integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from kitchenowl_python.exceptions import (
    KitchenOwlAuthException,
    KitchenOwlRequestException,
)
from kitchenowl_python.kitchenowl import KitchenOwl

from . import KitchenOwlConfigEntry
from .const import CONF_HOUSEHOLD, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="host")
        ),
        vol.Required(CONF_ACCESS_TOKEN): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="access_token")
        ),
        vol.Optional(CONF_VERIFY_SSL, default=True): bool,
    }
)
STEP_REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="access_token")
        ),
    }
)

_LOGGER = logging.getLogger(__name__)


class KitchenowlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Kitchenowl config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 0
    MINOR_VERSION = 1

    config_entry: KitchenOwlConfigEntry | None = None

    def __init__(self):
        """Initialise the KitchenOwl Config Flow."""

        self.data: dict[str, Any] = {}
        self.kitchenowl: KitchenOwl | None = None

    async def setup_connection(self, host, token, verify_ssl) -> KitchenOwl:
        """Set up and test the connection to the KitchenOwl instance."""

        session = async_get_clientsession(self.hass, verify_ssl=verify_ssl)
        kitchenowl = KitchenOwl(session, host, token)

        await kitchenowl.test_connection()

        return kitchenowl

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Invoke when a user initiates a flow via the user interface."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self.kitchenowl = await self.setup_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_ACCESS_TOKEN],
                    user_input[CONF_VERIFY_SSL],
                )

                self.data[CONF_HOST] = user_input[CONF_HOST]
                self.data[CONF_ACCESS_TOKEN] = user_input[CONF_ACCESS_TOKEN]
                self.data[CONF_VERIFY_SSL] = user_input[CONF_VERIFY_SSL]
            except KitchenOwlAuthException:
                errors["base"] = "invalid_access_token"
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except KitchenOwlRequestException:
                errors["base"] = "cannot_connect"
            if not errors:
                return await self.async_step_household()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_household(self, user_input: dict[str, Any] | None = None):
        """Second step in the config flow, letting the user select the household."""

        errors: dict[str, str] = {}
        step_household_schema = vol.Schema({})
        if user_input and user_input is not None:
            try:
                self.data[CONF_HOUSEHOLD] = user_input[CONF_HOUSEHOLD]
                assert self.kitchenowl

                user = await self.kitchenowl.get_user_info()

            except KitchenOwlAuthException:
                errors["base"] = "invalid_access_token"
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except KitchenOwlRequestException:
                errors["base"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(
                    f"{user["id"]}_{user_input[CONF_HOUSEHOLD]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="KitchenOwl", data=self.data)
        else:
            assert self.kitchenowl is not None
            try:
                households = await self.kitchenowl.get_households()
                if not households:
                    errors["base"] = "no_housheolds"
            except KitchenOwlAuthException:
                errors["base"] = "invalid_access_token"
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except KitchenOwlRequestException:
                errors["base"] = "cannot_connect"
            if not errors:
                household_options = [
                    SelectOptionDict(value=str(h["id"]), label=h["name"])
                    for h in households
                ]

                step_household_schema = vol.Schema(
                    {
                        vol.Required(
                            CONF_HOUSEHOLD, default=household_options[0]["value"]
                        ): SelectSelector(
                            SelectSelectorConfig(options=household_options),
                        ),
                    }
                )

        return self.async_show_form(
            step_id="household",
            data_schema=step_household_schema,
            errors=errors,
        )

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        self.config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        """Dialog that informs the user that reauth is required."""

        errors: dict[str, str] = {}

        assert self.config_entry

        if user_input and user_input is not None:
            try:
                self.kitchenowl = await self.setup_connection(
                    self.config_entry.data[CONF_HOST],
                    user_input[CONF_ACCESS_TOKEN],
                    self.config_entry.data[CONF_VERIFY_SSL],
                )
                user = await self.kitchenowl.get_user_info()
            except KitchenOwlAuthException:
                errors["base"] = "invalid_access_token"
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except KitchenOwlRequestException:
                errors["base"] = "cannot_connect"
            if not errors:
                if (
                    f"{user["id"]}_{self.config_entry.data[CONF_HOUSEHOLD]}"
                    == self.config_entry.unique_id
                ):
                    return self.async_update_reload_and_abort(
                        self.config_entry,
                        data={
                            **self.config_entry.data,
                            CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                        },
                        reason="reauth_successful",
                    )
                return self.async_abort(reason="reconfig_different_user")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Handle reconfiguration of the integration."""

        self.config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Handle reconfiguration."""

        errors: dict[str, str] = {}

        assert self.config_entry

        if user_input is not None:
            try:
                self.kitchenowl = await self.setup_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_ACCESS_TOKEN],
                    user_input[CONF_VERIFY_SSL],
                )
                user = await self.kitchenowl.get_user_info()
            except KitchenOwlAuthException:
                errors["base"] = "invalid_access_token"
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except KitchenOwlRequestException:
                errors["base"] = "cannot_connect"
            if not errors:
                if (
                    f"{user["id"]}_{self.config_entry.data[CONF_HOUSEHOLD]}"
                    == self.config_entry.unique_id
                ):
                    return self.async_update_reload_and_abort(
                        self.config_entry,
                        data={
                            **self.config_entry.data,
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                            CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                        },
                        reason="reconfigure_successful",
                    )
                return self.async_abort(reason="reconfig_different_user")

        step_reconfigure_user_data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST, default=self.config_entry.data[CONF_HOST]
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="host")
                ),
                vol.Required(
                    CONF_ACCESS_TOKEN, default=self.config_entry.data[CONF_ACCESS_TOKEN]
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT, autocomplete="access_token"
                    )
                ),
                vol.Optional(
                    CONF_VERIFY_SSL,
                    default=self.config_entry.data.get(CONF_VERIFY_SSL, True),
                ): bool,
            }
        )
        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=step_reconfigure_user_data_schema,
            errors=errors,
        )
