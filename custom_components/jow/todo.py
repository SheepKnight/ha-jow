"""Todo platform for Jow integration."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set

from homeassistant.components.todo import (
    TodoListEntity,
    TodoListEntityFeature,
    TodoItem,
    TodoItemStatus,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def format_recipe(meal: Dict[str, Any]) -> Dict[str, Any]:
    """Format meal/recipe dictionary into a clean JSON structure."""
    rec = meal.get("recipe") or {}
    rec_id = str(rec.get("id") or rec.get("_id") or meal.get("id") or "")
    image_rel = rec.get("imageUrl") or meal.get("imageUrl")
    image_url = f"https://static.jow.fr/{image_rel}" if image_rel else None
    url = f"https://jow.fr/recipes/{rec_id}" if rec_id else None

    # Parse constituents / ingredients if available
    ingredients: List[Dict[str, Any]] = []
    constituents = rec.get("constituents") or rec.get("ingredients") or []
    for c in constituents:
        if not isinstance(c, dict):
            continue
        ing = c.get("ingredient") or {}
        name = ing.get("name") or c.get("name")
        if name:
            unit_info = c.get("unit")
            unit_name = unit_info.get("name") if isinstance(unit_info, dict) else None
            ingredients.append({
                "name": name,
                "quantity": c.get("quantityPerCover"),
                "unit": unit_name,
            })

    author = rec.get("author") or {}
    author_name = (
        author.get("name")
        or author.get("jowProfile", {}).get("displayName")
        if isinstance(author, dict)
        else None
    )

    is_cooked = bool(meal.get("isCooked", False))

    return {
        "id": rec_id,
        "title": rec.get("title") or meal.get("title") or "Unknown Recipe",
        "covers": meal.get("coversCount", 2),
        "cooking_time": rec.get("cookingTime"),
        "preparation_time": rec.get("preparationTime"),
        "image_url": image_url,
        "recipe_url": url,
        "author": author_name,
        "ingredients": ingredients,
        "is_cooked": is_cooked,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jow Todo platform."""
    coordinator: JowDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        JowRecipesToCookTodoList(coordinator, entry),
        JowPendingMenuTodoList(coordinator, entry),
    ]

    async_add_entities(entities)


class JowBaseTodoList(CoordinatorEntity[JowDataUpdateCoordinator], TodoListEntity):
    """Base class for Jow recipe todo lists."""

    _attr_has_entity_name = True
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(
        self,
        coordinator: JowDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the todo list."""
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.unique_id}_todo_{key}"
        self._attr_icon = icon
        self._completed_uids: Set[str] = set()
        self._uncompleted_uids: Set[str] = set()

    @property
    def letscook_data(self) -> Dict[str, Any]:
        """Return letscook dictionary from coordinator."""
        return self.coordinator.data.get("letscook", {}) if self.coordinator.data else {}

    def _get_raw_meals(self) -> List[Dict[str, Any]]:
        """Override in subclasses to return raw meals list."""
        raise NotImplementedError

    def get_formatted_recipes(self) -> List[Dict[str, Any]]:
        """Return formatted recipes list."""
        return [format_recipe(m) for m in self._get_raw_meals()]

    @property
    def todo_items(self) -> Optional[List[TodoItem]]:
        """Return current items in the todo list."""
        items: List[TodoItem] = []
        for r in self.get_formatted_recipes():
            uid = r["id"] or r["title"]
            time_parts = []
            if r.get("preparation_time"):
                time_parts.append(f"Prep: {r['preparation_time']}m")
            if r.get("cooking_time"):
                time_parts.append(f"Cook: {r['cooking_time']}m")
            time_desc = " | ".join(time_parts)

            desc = f"{r.get('covers', 2)} portions"
            if time_desc:
                desc += f" • {time_desc}"
            if r.get("recipe_url"):
                desc += f" • {r['recipe_url']}"

            is_cooked = r.get("is_cooked", False)
            if uid in self._completed_uids:
                is_cooked = True
            elif uid in self._uncompleted_uids:
                is_cooked = False

            status = (
                TodoItemStatus.COMPLETED
                if is_cooked
                else TodoItemStatus.NEEDS_ACTION
            )

            items.append(
                TodoItem(
                    summary=r["title"],
                    uid=uid,
                    status=status,
                    description=desc,
                )
            )
        return items

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes including JSON output."""
        recipes = self.get_formatted_recipes()
        remaining = [r for r in recipes if not r.get("is_cooked")]
        cooked = [r for r in recipes if r.get("is_cooked")]
        return {
            "count": len(remaining),
            "total_count": len(recipes),
            "remaining_count": len(remaining),
            "cooked_count": len(cooked),
            "recipes": recipes,
            "remaining_recipes": remaining,
            "recipes_json": json.dumps(recipes, ensure_ascii=False),
        }

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item status (mark as completed or needs action)."""
        if item.uid:
            if item.status == TodoItemStatus.COMPLETED:
                self._completed_uids.add(item.uid)
                self._uncompleted_uids.discard(item.uid)
            elif item.status == TodoItemStatus.NEEDS_ACTION:
                self._uncompleted_uids.add(item.uid)
                self._completed_uids.discard(item.uid)
            self.async_write_ha_state()


class JowRecipesToCookTodoList(JowBaseTodoList):
    """Todo list for recipes queued to cook."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator,
            entry,
            "recipes_to_cook",
            "Jow Recipes to Cook",
            "mdi:chef-hat",
        )

    def _get_raw_meals(self) -> List[Dict[str, Any]]:
        section = self.letscook_data.get("recipesToCook") or {}
        return section.get("meals") or section.get("recipes") or []


class JowPendingMenuTodoList(JowBaseTodoList):
    """Todo list for meals in the planned / pending menu."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator,
            entry,
            "pending_menu",
            "Jow Planned Menu",
            "mdi:silverware-fork-knife",
        )

    def _get_raw_meals(self) -> List[Dict[str, Any]]:
        section = self.letscook_data.get("pendingMenu") or {}
        return section.get("meals") or section.get("recipes") or []
