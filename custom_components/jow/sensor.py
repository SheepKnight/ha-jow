"""Sensor platform for Jow integration."""

import json
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JowDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jow sensor entities based on a config entry."""
    coordinator: JowDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        JowPendingMenuSensor(coordinator, entry),
        JowRecipesToCookSensor(coordinator, entry),
        JowSharedRecipesSensor(coordinator, entry),
        JowCollectionsSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class JowBaseSensor(CoordinatorEntity[JowDataUpdateCoordinator], SensorEntity):
    """Base sensor for Jow."""

    def __init__(
        self,
        coordinator: JowDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._attr_name = f"Jow {name}"
        self._attr_unique_id = f"{entry.unique_id}_{sensor_key}"
        self._attr_icon = icon

    @property
    def letscook_data(self) -> Dict[str, Any]:
        """Get letscook data from coordinator."""
        return self.coordinator.data.get("letscook", {}) if self.coordinator.data else {}


class JowPendingMenuSensor(JowBaseSensor):
    """Sensor for currently pending / planned menu meals."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "pending_menu", "Pending Menu", "mdi:silverware-fork-knife")

    @property
    def native_value(self) -> int:
        """Return the number of remaining (uncooked) meals in the pending menu."""
        menu = self.letscook_data.get("pendingMenu") or {}
        meals = menu.get("meals") or menu.get("recipes") or []
        return len([m for m in meals if not m.get("isCooked", False)])

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the list of meals as JSON-serializable list and JSON string."""
        from .todo import format_recipe
        menu = self.letscook_data.get("pendingMenu") or {}
        meals = menu.get("meals") or menu.get("recipes") or []
        formatted = [format_recipe(m) for m in meals]
        remaining = [r for r in formatted if not r.get("is_cooked")]
        cooked = [r for r in formatted if r.get("is_cooked")]
        return {
            "count": len(remaining),
            "total_count": len(formatted),
            "remaining_count": len(remaining),
            "cooked_count": len(cooked),
            "recipes": formatted,
            "remaining_recipes": remaining,
            "recipes_json": json.dumps(formatted, ensure_ascii=False),
        }


class JowRecipesToCookSensor(JowBaseSensor):
    """Sensor for recipes queued up to cook."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "recipes_to_cook", "Recipes to Cook", "mdi:chef-hat")

    @property
    def native_value(self) -> int:
        """Return the count of remaining (uncooked) recipes to cook."""
        recipes_data = self.letscook_data.get("recipesToCook") or {}
        meals = recipes_data.get("meals") or recipes_data.get("recipes") or []
        return len([m for m in meals if not m.get("isCooked", False)])

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the list of recipes to cook as JSON-serializable list and JSON string."""
        from .todo import format_recipe
        recipes_data = self.letscook_data.get("recipesToCook") or {}
        meals = recipes_data.get("meals") or recipes_data.get("recipes") or []
        formatted = [format_recipe(m) for m in meals]
        remaining = [r for r in formatted if not r.get("is_cooked")]
        cooked = [r for r in formatted if r.get("is_cooked")]
        return {
            "count": len(remaining),
            "total_count": len(formatted),
            "remaining_count": len(remaining),
            "cooked_count": len(cooked),
            "recipes": formatted,
            "remaining_recipes": remaining,
            "recipes_json": json.dumps(formatted, ensure_ascii=False),
        }



class JowSharedRecipesSensor(JowBaseSensor):
    """Sensor for community shared recipes."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "shared_recipes", "Shared Recipes", "mdi:account-group")

    @property
    def native_value(self) -> int:
        """Return the count of shared recipes retrieved."""
        shared = self.letscook_data.get("sharedRecipes") or {}
        meals = shared.get("meals") or []
        return len(meals)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return details of shared recipes as JSON objects."""
        shared = self.letscook_data.get("sharedRecipes") or {}
        meals = shared.get("meals") or []
        items = []
        for m in meals:
            rec = m.get("recipe") or {}
            author = rec.get("author") or {}
            author_name = author.get("name") or author.get("jowProfile", {}).get("displayName") or "Jow"
            items.append({
                "title": rec.get("title"),
                "id": rec.get("id") or rec.get("_id"),
                "author": author_name,
                "covers": m.get("coversCount", 2),
                "cooking_time": rec.get("cookingTime"),
                "preparation_time": rec.get("preparationTime"),
            })
        return {
            "recipes": items,
            "has_more": shared.get("hasMore", False),
        }


class JowCollectionsSensor(JowBaseSensor):
    """Sensor for user collections (Favorites, Try Later, etc.)."""

    def __init__(self, coordinator: JowDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "collections", "Collections", "mdi:bookmark-multiple")

    @property
    def native_value(self) -> int:
        """Return the count of collections."""
        col_data = self.letscook_data.get("collections") or {}
        collections = col_data.get("collections") or []
        return len(collections)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the user collections as JSON objects."""
        col_data = self.letscook_data.get("collections") or {}
        collections = col_data.get("collections") or []
        items = []
        for c in collections:
            items.append({
                "id": c.get("id"),
                "title": c.get("title"),
                "type": c.get("type"),
                "recipe_count": c.get("recipeCount", 0),
            })
        return {"collections": items}
