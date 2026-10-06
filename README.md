# Jow for Home Assistant (HACS Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)

A custom Home Assistant integration for **[Jow.fr](https://jow.fr)**. 
Integrate your Jow planned menus, recipes to cook, collections/favorites, and shared recipes directly into Home Assistant.

## ✨ Features

- **Authentication Flow**: 1-click Web Login Helper or manual token entry with automatic silent token refresh.
- **Data Coordinator**: Periodically updates cooking plans and user profile in the background.
- **To-Do Lists (`todo`)**:
  - `todo.jow_recipes_to_cook`: Remaining recipes to cook in Home Assistant's native To-do list dashboard (supports checking off items).
  - `todo.jow_pending_menu`: Planned meals in your active menu.
- **Sensors with JSON Lists**:
  - `sensor.jow_pending_menu`: Count and details of meals in your pending menu.
  - `sensor.jow_recipes_to_cook`: Count and details of recipes queued to cook.
  - `sensor.jow_shared_recipes`: Community & shared recipes list.
  - `sensor.jow_collections`: User collections (Favorites, To try later, etc.).
- **JSON List Access Everywhere**:
  - **Entity Attributes**: `state_attr('todo.jow_recipes_to_cook', 'recipes')` or `state_attr(..., 'recipes_json')`.
  - **Home Assistant Action**: `jow.get_recipes` (with `category: recipes_to_cook | pending_menu | all`) returns structured JSON data into scripts and automations.
  - **Direct HTTP API**: `GET https://<your-ha-url>/api/jow/recipes` returns raw JSON directly for external tools, widgets, and scripts.


## 📦 Installation via HACS

1. In Home Assistant, open **HACS** $\rightarrow$ **Integrations**.
2. Click the three dots in the top-right corner $\rightarrow$ **Custom repositories**.
3. Add repository URL: `https://github.com/SheepKnight/ha-jow` with category **Integration**.
4. Click **Download**, then restart Home Assistant.

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration**.
2. Search for **Jow**.
3. Enter your **Device ID** and **Refresh Token** (obtained from browser DevTools or session storage).

---

Developed by [@SheepKnight](https://github.com/SheepKnight).
