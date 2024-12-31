"""Data Update Coordinator for the KitchenOwl integration."""

import logging
from datetime import timedelta
from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from kitchenowl_python.exceptions import (
    KitchenOwlAuthException,
    KitchenOwlException,
    KitchenOwlRequestException,
)
from kitchenowl_python.kitchenowl import KitchenOwl
from kitchenowl_python.types import KitchenOwlShoppingList, KitchenOwlShoppingListItem

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ShoppingListData(TypedDict):
    """Data class to conveniently access all shopping list data."""

    shopping_list: KitchenOwlShoppingList
    items: list[KitchenOwlShoppingListItem]
    recent_items: list[KitchenOwlShoppingListItem]


class KitchenOwlDataUpdateCoordinator(
    DataUpdateCoordinator[dict[int, ShoppingListData]]
):
    """Coordinator to manage fetching / updating KitchenOwl data."""

    def __init__(
        self, hass: HomeAssistant, kitchenowl: KitchenOwl, household_id: str
    ) -> None:
        """Initialise the coordinator with Home Asisstant and KitchenOwl."""
        interval = timedelta(seconds=SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )
        self.kitchenowl = kitchenowl
        self._household_id = household_id

    async def _async_update_data(self) -> dict[int, ShoppingListData]:
        try:
            lists_response = await self.kitchenowl.get_shoppinglists(self._household_id)
        except KitchenOwlAuthException as e:
            raise UpdateFailed("Unable to get kitchenowl data") from e
        except TimeoutError as e:
            raise UpdateFailed("Unable to get kitchenowl data") from e
        except KitchenOwlRequestException as e:
            raise UpdateFailed("Unable to get kitchenowl data") from e
        except KitchenOwlException as e:
            raise UpdateFailed("Unable to get kitchenowl data") from e

        list_data: dict[int, ShoppingListData] = {}
        for lst in lists_response:
            try:
                items = await self.kitchenowl.get_shoppinglist_items(lst["id"])
                recent_items = await self.kitchenowl.get_shoppinglist_recent_items(
                    lst["id"]
                )
            except KitchenOwlAuthException as e:
                raise UpdateFailed("Unable to get kitchenowl data") from e
            except TimeoutError as e:
                raise UpdateFailed("Unable to get kitchenowl data") from e
            except KitchenOwlRequestException as e:
                raise UpdateFailed("Unable to get kitchenowl data") from e
            except KitchenOwlException as e:
                raise UpdateFailed("Unable to get kitchenowl data") from e
            else:
                list_data[lst["id"]] = ShoppingListData(
                    shopping_list=lst, items=items, recent_items=recent_items
                )
        return list_data
