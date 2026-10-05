"""HTTP Views for Jow Web Login in Home Assistant."""

import logging
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JowApiClient, JowAuthError
from .const import CONF_DEVICE_ID, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

VIEW_LOGIN_URL = "/api/jow/login"
VIEW_CALLBACK_URL = "/api/jow/callback"

LOGIN_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connect Jow to Home Assistant</title>
  <style>
    :root {
      --primary: #FF5C39;
      --bg: #121820;
      --card-bg: #1C2430;
      --text: #F3F4F6;
      --muted: #9CA3AF;
      --success: #10B981;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 1rem;
      box-sizing: border-box;
    }
    .card {
      background: var(--card-bg);
      border-radius: 1rem;
      padding: 2rem;
      max-width: 540px;
      width: 100%;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    h1 {
      margin-top: 0;
      font-size: 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--primary);
    }
    p {
      color: var(--muted);
      line-height: 1.5;
    }
    .step {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 0.5rem;
      padding: 1rem;
      margin: 1rem 0;
    }
    .step-number {
      font-weight: bold;
      color: var(--primary);
      margin-right: 0.5rem;
    }
    .bookmarklet-btn {
      display: inline-block;
      background: var(--primary);
      color: white;
      text-decoration: none;
      padding: 0.75rem 1.25rem;
      border-radius: 0.5rem;
      font-weight: 600;
      cursor: grab;
      margin: 0.5rem 0;
      user-select: none;
    }
    .btn-manual {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      cursor: pointer;
      margin-top: 0.5rem;
    }
    textarea {
      width: 100%;
      box-sizing: border-box;
      background: #111827;
      color: #E5E7EB;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 0.75rem;
      font-family: monospace;
      font-size: 0.85rem;
      resize: vertical;
    }
    #status {
      display: none;
      padding: 1rem;
      border-radius: 0.5rem;
      margin-top: 1rem;
      font-weight: 600;
      text-align: center;
    }
    #status.success {
      display: block;
      background: rgba(16, 185, 129, 0.2);
      border: 1px solid var(--success);
      color: var(--success);
    }
    #status.error {
      display: block;
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid #EF4444;
      color: #EF4444;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>🍳 Connect Jow to Home Assistant</h1>
    <p>Because Jow supports multiple login methods (Google, Apple, Email), use this 1-click helper to securely pair your session.</p>

    <div class="step">
      <div><span class="step-number">Step 1</span>Drag this button to your browser Bookmarks Bar:</div>
      <div style="text-align: center; margin: 0.75rem 0;">
        <a class="bookmarklet-btn" href="javascript:%%BOOKMARKLET_CODE%%">⭐ Connect to Home Assistant</a>
      </div>
      <div style="font-size: 0.85rem; color: var(--muted);">Or keep it handy on your bookmarks bar.</div>
    </div>

    <div class="step">
      <div><span class="step-number">Step 2</span>Open <a href="https://jow.fr/cooking" target="_blank" style="color: var(--primary);">jow.fr</a> and make sure you are logged in.</div>
    </div>

    <div class="step">
      <div><span class="step-number">Step 3</span>While viewing Jow in your browser, click the bookmarklet!</div>
      <p style="font-size: 0.85rem; margin-bottom: 0;">It securely extracts your local session and connects directly to Home Assistant.</p>
    </div>

    <details style="margin-top: 1.5rem;">
      <summary style="cursor: pointer; color: var(--muted); font-size: 0.9rem;">Advanced: Manual paste</summary>
      <div style="margin-top: 0.5rem;">
        <textarea id="manualInput" rows="3" placeholder='Paste {"deviceId": "...", "refreshToken": "..."}'></textarea>
        <button class="btn-manual" onclick="submitManual()">Submit Credentials</button>
      </div>
    </details>

    <div id="status"></div>
  </div>

  <script>
    function showStatus(text, isSuccess) {
      const el = document.getElementById('status');
      el.className = isSuccess ? 'success' : 'error';
      el.textContent = text;
    }

    async function submitManual() {
      try {
        const text = document.getElementById('manualInput').value.trim();
        const json = JSON.parse(text);
        const resp = await fetch('/api/jow/callback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(json)
        });
        const res = await resp.json();
        if (resp.ok) {
          showStatus('✅ Successfully connected! You can now return to Home Assistant.', true);
        } else {
          showStatus('❌ ' + (res.error || 'Failed to authenticate with Jow'), false);
        }
      } catch (e) {
        showStatus('❌ Invalid JSON or network error: ' + e.message, false);
      }
    }
  </script>
</body>
</html>
"""


def build_bookmarklet_code(host_url: str) -> str:
    """Build the javascript bookmarklet code that runs on jow.fr."""
    js = f"""(function(){{
      try {{
        const el = document.getElementById('__next') || document.body;
        const key = Object.keys(el).find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
        let queue = [el[key]];
        let state = null;
        while (queue.length > 0) {{
          let node = queue.shift();
          if (!node) continue;
          if (node.memoizedProps?.store?.getState) {{
            state = node.memoizedProps.store.getState();
            break;
          }}
          if (node.child) queue.push(node.child);
          if (node.sibling) queue.push(node.sibling);
        }}
        if (!state?.auth?.refreshToken) {{
          alert('Could not find active Jow session. Please log in on jow.fr first!');
          return;
        }}
        const deviceId = state.deviceFingerprint || state.fingerprint?.deviceFingerprint || state.auth?.deviceId || 'web:auto';
        const refreshToken = state.auth.refreshToken;

        fetch('{host_url}/api/jow/callback', {{
          method: 'POST',
          mode: 'cors',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ deviceId: deviceId, refreshToken: refreshToken }})
        }}).then(res => res.json()).then(data => {{
          if (data.success) {{
            alert('🎉 Jow successfully connected as ' + data.user_name + '! Return to Home Assistant to finish setup.');
          }} else {{
            alert('Error connecting to Home Assistant: ' + (data.error || 'Unknown error'));
          }}
        }}).catch(err => {{
          alert('Network error connecting to Home Assistant: ' + err.message);
        }});
      }} catch (err) {{
        alert('Failed to read Jow session: ' + err.message);
      }}
    }})();"""
    return js.replace("\n", "").replace("  ", "")



class JowLoginView(HomeAssistantView):
    """View to render the Jow web login helper page."""

    url = VIEW_LOGIN_URL
    name = "api:jow:login"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        """Render the webview helper page."""
        hass: HomeAssistant = request.app["hass"]
        # Use the configured internal/external URL or fallback to Host header
        host = request.headers.get("Host", "localhost:8123")
        scheme = request.scheme or "http"
        host_url = f"{scheme}://{host}"

        bookmarklet_code = build_bookmarklet_code(host_url)
        content = LOGIN_HTML_PAGE.replace("%%BOOKMARKLET_CODE%%", bookmarklet_code)

        return web.Response(text=content, content_type="text/html")


class JowCallbackView(HomeAssistantView):
    """View to receive credentials from the browser bookmarklet or web view."""

    url = VIEW_CALLBACK_URL
    name = "api:jow:callback"
    requires_auth = False

    # Allow CORS requests from jow.fr
    cors_allowed = True

    async def post(self, request: web.Request) -> web.Response:
        """Handle incoming token payload."""
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        device_id = body.get("deviceId") or body.get("device_id")
        refresh_token = body.get("refreshToken") or body.get("refresh_token")

        if not refresh_token:
            return web.json_response({"error": "Missing refreshToken in payload"}, status=400)

        if not device_id:
            device_id = "web:homeassistant"

        # Validate against Jow API
        session = async_get_clientsession(hass)
        client = JowApiClient(session, device_id=device_id, refresh_token=refresh_token)

        try:
            await client.async_refresh_access_token()
            profile = await client.async_get_profile()
            user_name = (
                profile.get("jowProfile", {}).get("firstName")
                or profile.get("jowProfile", {}).get("email")
                or "Jow User"
            )
        except JowAuthError as err:
            _LOGGER.warning("Jow callback auth error: %s", err)
            return web.json_response({"error": f"Invalid credentials: {err}"}, status=401)
        except Exception as err:
            _LOGGER.error("Jow callback validation error: %s", err)
            return web.json_response({"error": f"Connection error: {err}"}, status=500)

        # Store pending credentials in hass.data so config flow can claim them
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["latest_web_auth"] = {
            CONF_DEVICE_ID: device_id,
            CONF_REFRESH_TOKEN: refresh_token,
            "user_name": user_name,
        }

        return web.json_response({
            "success": True,
            "user_name": user_name,
        }, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    async def options(self, request: web.Request) -> web.Response:
        """Handle CORS preflight options request."""
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
