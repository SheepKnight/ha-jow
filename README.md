# Jow for Home Assistant (HACS Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)

A custom Home Assistant integration for **[Jow.fr](https://jow.fr)**. 
Integrate your Jow planned menus, recipes to cook, collections/favorites, and shared recipes directly into Home Assistant.

## ✨ Features

- **Authentication Flow**: Login using your Jow session credentials with automatic token refresh.
- **Data Coordinator**: Periodically updates cooking plans and user profile in the background.
- **Sensors with JSON Lists**:
  - `sensor.jow_pending_menu`: Count and details of meals in your pending menu.
  - `sensor.jow_recipes_to_cook`: Count and details of recipes queued to cook.
  - `sensor.jow_shared_recipes`: Community & shared recipes list.
  - `sensor.jow_collections`: User collections (Favorites, To try later, etc.).

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
