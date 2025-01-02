"""Todo shopping list platform for KitchenOwl."""

import asyncio
import logging
from typing import TYPE_CHECKING

from kitchenowl_python.types import KitchenOwlItem, KitchenOwlShoppingListItem

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KitchenOwlConfigEntry
from .coordinator import KitchenOwlDataUpdateCoordinator, ShoppingListData

_LOGGER = logging.getLogger(__name__)


def _convert_kitchenowl_item_to_todo(
    item: KitchenOwlShoppingListItem, completed: bool = True
) -> TodoItem:
    return TodoItem(
        uid=str(item["id"]),  # homeassistant expects str for item uids
        summary=item["name"],
        description=item["description"] or "",
        status=TodoItemStatus.COMPLETED if completed else TodoItemStatus.NEEDS_ACTION,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KitchenOwlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the entry."""

    coordinator: KitchenOwlDataUpdateCoordinator = entry.runtime_data

    unique_id = entry.unique_id

    if TYPE_CHECKING:
        assert unique_id

    async_add_entities(
        KitchenOwlTodoListEntity(coordinator, list_data, unique_id)
        for list_data in coordinator.data.values()
    )


class KitchenOwlTodoListEntity(
    CoordinatorEntity[KitchenOwlDataUpdateCoordinator], TodoListEntity
):
    """TodoList entity using KitchenOwl."""

    _attr_translation_key = "shopping_list"
    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(
        self,
        coordinator: KitchenOwlDataUpdateCoordinator,
        shopping_list_data: ShoppingListData,
        entry_unique_id: str,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""

        super().__init__(coordinator=coordinator)
        self._shoppinglist_id = shopping_list_data["shopping_list"]["id"]
        self._attr_unique_id = (
            f"{entry_unique_id}_{shopping_list_data["shopping_list"]["id"]}"
        )
        self._attr_name = shopping_list_data["shopping_list"]["name"]

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the todo items."""
        return [
            *(
                _convert_kitchenowl_item_to_todo(item, False)
                for item in sorted(
                    self.shopping_list["items"],
                    key=lambda i: i["ordering"] if "ordering" in i else i["id"],
                )
            ),
            *(
                _convert_kitchenowl_item_to_todo(item, True)
                for item in sorted(
                    self.shopping_list["recent_items"],
                    key=lambda i: i["ordering"] if "ordering" in i else i["id"],
                )
            ),
        ]

    @property
    def shopping_list(
        self,
    ) -> ShoppingListData:
        """Return the kitchenowl list."""
        return self.coordinator.data[self._shoppinglist_id]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new shoppinglist item."""

        if item.status != TodoItemStatus.NEEDS_ACTION:
            raise ValueError("Only active tasks may be created.")
        if item.summary is None:
            raise ValueError("Summary cannot be None")
        await self.coordinator.kitchenowl.add_shoppinglist_item(
            list_id=self._shoppinglist_id, item_name=item.summary
        )
        await self.coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an existing shoppinglist item."""

        if item.uid is None:
            raise KeyError("uid not set")

        current_item = next(
            (
                _convert_kitchenowl_item_to_todo(
                    i, i in self.shopping_list["recent_items"]
                )
                for i in self.shopping_list["items"]
                + self.shopping_list["recent_items"]
                if str(i["id"]) == item.uid
            ),
            None,
        )
        # change the item on summary change - only if completed
        if (
            current_item is not None
            and current_item.summary != item.summary
            and item.status != TodoItemStatus.COMPLETED
        ):
            if item.summary is None:
                raise ValueError("Summary cannot be None")
            kitchenowl_item = KitchenOwlItem(id=int(item.uid), name=item.summary)
            await self.coordinator.kitchenowl.update_item(
                item_id=int(item.uid), item=kitchenowl_item
            )

        if current_item is not None and current_item.description != item.description:
            await self.coordinator.kitchenowl.update_shoppinglist_item_description(
                list_id=self._shoppinglist_id,
                item_id=int(item.uid),
                item_description=item.description
                if item.description is not None
                else "",
            )

        if current_item is not None and current_item.status != item.status:
            if item.status == TodoItemStatus.COMPLETED:
                await self.coordinator.kitchenowl.remove_shoppinglist_item(
                    list_id=self._shoppinglist_id,
                    item_id=int(item.uid),
                )
            else:  # set the item back on the list
                if item.summary is None:
                    raise ValueError("Summary cannot be None")
                await self.coordinator.kitchenowl.add_shoppinglist_item(
                    list_id=self._shoppinglist_id,
                    item_name=item.summary,
                    item_description=item.description
                    if item.description is not None
                    else "",
                )
        await self.coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Remove a shoppinglist item from the list."""

        await asyncio.gather(
            *[self.coordinator.kitchenowl.delete_item(item_id=int(uid)) for uid in uids]
        )
        await self.coordinator.async_refresh()

    async def async_added_to_hass(self) -> None:
        """Update when the list is added to hass."""

        await super().async_added_to_hass()
        self._handle_coordinator_update()
