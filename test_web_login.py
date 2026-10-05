"""
Standalone test script for Jow Web Login Helper.
Runs a local server mimicking Home Assistant's /api/jow/login and /api/jow/callback.
"""

import asyncio
import importlib.util
import json
import logging
import os
import sys
import types
import webbrowser
import aiohttp
from aiohttp import web

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_LOGGER = logging.getLogger("test_web_login")

# Dynamically import JowApiClient from custom_components without requiring Home Assistant installed
const = types.ModuleType("custom_components.jow.const")
const.AUTH_URL = "https://api.jow.fr/public/auth?createIfNotExist=true"
const.BASE_API_URL = "https://api.jow.fr/public"
sys.modules["custom_components.jow.const"] = const

api_path = os.path.join(os.path.dirname(__file__), "custom_components", "jow", "api.py")
spec = importlib.util.spec_from_file_location("custom_components.jow.api", api_path)
api_module = importlib.util.module_from_spec(spec)
api_module.__package__ = "custom_components.jow"
spec.loader.exec_module(api_module)
JowApiClient = api_module.JowApiClient

PORT = 8123
HOST = "localhost"

# Read the HTML template from view.py or embed directly
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jow Home Assistant Login Tester</title>
  <style>
    :root {
      --primary: #FF5C39;
      --primary-hover: #E04D2B;
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
      padding: 1.5rem;
      box-sizing: border-box;
    }
    .card {
      background: var(--card-bg);
      border-radius: 1rem;
      padding: 2rem;
      max-width: 580px;
      width: 100%;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    h1 {
      margin-top: 0;
      font-size: 1.6rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      color: var(--primary);
    }
    p {
      color: var(--muted);
      line-height: 1.5;
      margin: 0.5rem 0 1.25rem 0;
    }
    .method-box {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 0.75rem;
      padding: 1.25rem;
      margin-bottom: 1.25rem;
    }
    .method-title {
      font-weight: 600;
      font-size: 1.05rem;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
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
      margin: 0.75rem 0;
      transition: background 0.2s;
    }
    .bookmarklet-btn:hover {
      background: var(--primary-hover);
    }
    .code-box {
      background: #0D1117;
      border: 1px solid #30363D;
      border-radius: 0.5rem;
      padding: 0.75rem;
      font-family: monospace;
      font-size: 0.8rem;
      color: #58A6FF;
      word-break: break-all;
      margin: 0.5rem 0;
      position: relative;
    }
    .btn {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.2s;
    }
    .btn:hover {
      background: rgba(255, 255, 255, 0.2);
    }
    #status {
      display: none;
      padding: 1rem;
      border-radius: 0.5rem;
      margin-top: 1.25rem;
      font-weight: 600;
      text-align: center;
    }
    #status.success {
      display: block;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid var(--success);
      color: var(--success);
    }
    #status.error {
      display: block;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid #EF4444;
      color: #EF4444;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>🍳 Jow Login Tester</h1>
    <p>Test the Home Assistant Web Login flow with your active browser session on <strong>jow.fr</strong>.</p>

    <!-- Method A: Bookmarklet -->
    <div class="method-box">
      <div class="method-title">⭐ Method 1: 1-Click Bookmarklet (Easiest)</div>
      <div style="font-size: 0.9rem; color: var(--muted);">1. Drag this button to your browser Bookmarks Bar:</div>
      <div style="text-align: center;">
        <a class="bookmarklet-btn" href="javascript:%%BOOKMARKLET_CODE%%">🔗 Link Jow to Home Assistant</a>
      </div>
      <div style="font-size: 0.85rem; color: var(--muted);">
        2. Open <a href="https://jow.fr/cooking" target="_blank" style="color: var(--primary);">jow.fr/cooking</a> (logged in).<br>
        3. Click the bookmarklet on that page!
      </div>
    </div>

    <!-- Method B: Console Snippet -->
    <div class="method-box">
      <div class="method-title">💻 Method 2: Console Snippet (No bookmarklet needed)</div>
      <div style="font-size: 0.85rem; color: var(--muted);">
        Open <a href="https://jow.fr/cooking" target="_blank" style="color: var(--primary);">jow.fr/cooking</a>, press <strong>F12</strong> &rarr; <strong>Console</strong>, paste and run:
      </div>
      <div class="code-box" id="snippetCode">%%SNIPPET_CODE%%</div>
      <button class="btn" onclick="copySnippet()">📋 Copy Snippet</button>
    </div>

    <div id="status"></div>
  </div>

  <script>
    function copySnippet() {
      const code = document.getElementById('snippetCode').textContent;
      navigator.clipboard.writeText(code).then(() => {
        alert('Snippet copied to clipboard! Paste it into your browser DevTools Console on jow.fr');
      });
    }

    function showStatus(text, isSuccess) {
      const el = document.getElementById('status');
      el.className = isSuccess ? 'success' : 'error';
      el.textContent = text;
    }

    // Poll server to check if auth succeeded
    const checkInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/jow/status');
        const data = await res.json();
        if (data.authenticated) {
          clearInterval(checkInterval);
          showStatus('🎉 Successfully authenticated as: ' + data.user_name + '! You can return to your terminal.', true);
        }
      } catch(e) {}
    }, 1500);
  </script>
</body>
</html>
"""


class TestLoginServer:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_get("/api/jow/login", self.handle_login_page)
        self.app.router.add_post("/api/jow/callback", self.handle_callback)
        self.app.router.add_options("/api/jow/callback", self.handle_options)
        self.app.router.add_get("/api/jow/status", self.handle_status)
        self.runner = None
        self.site = None
        self.authenticated_user = None
        self.auth_event = asyncio.Event()

    def _get_js_payload(self) -> str:
        callback_url = f"http://{HOST}:{PORT}/api/jow/callback"
        return f"""(function(){{
  try {{
    let d = localStorage.getItem('jow:auth:deviceId') || localStorage.getItem('deviceId');
    let r = localStorage.getItem('jow:auth:refreshToken') || localStorage.getItem('refreshToken');
    if (!r) {{
      for (let i = 0; i < localStorage.length; i++) {{
        let k = localStorage.key(i);
        let v = localStorage.getItem(k);
        if (v && v.includes('refreshToken')) {{
          try {{
            let parsed = JSON.parse(v);
            r = parsed.refreshToken || r;
            d = parsed.deviceId || d;
          }} catch(e) {{}}
        }}
      }}
    }}
    if (!r) {{
      alert('Could not find active Jow session. Please log in on jow.fr first!');
      return;
    }}
    fetch('{callback_url}', {{
      method: 'POST',
      mode: 'cors',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ deviceId: d || 'web:auto', refreshToken: r }})
    }}).then(res => res.json()).then(data => {{
      if (data.success) {{
        alert('🎉 Jow successfully connected as ' + data.user_name + '! Return to your terminal.');
      }} else {{
        alert('Error: ' + (data.error || 'Unknown error'));
      }}
    }}).catch(err => {{
      alert('Network error connecting to helper: ' + err.message);
    }});
  }} catch (err) {{
    alert('Failed to read Jow session: ' + err.message);
  }}
}})();"""

    async def handle_login_page(self, request: web.Request) -> web.Response:
        raw_js = self._get_js_payload()
        min_js = raw_js.replace("\n", "").replace("  ", "")
        html = HTML_TEMPLATE.replace("%%BOOKMARKLET_CODE%%", min_js).replace("%%SNIPPET_CODE%%", min_js)
        return web.Response(text=html, content_type="text/html")

    async def handle_options(self, request: web.Request) -> web.Response:
        return web.Response(headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    async def handle_status(self, request: web.Request) -> web.Response:
        if self.authenticated_user:
            return web.json_response({
                "authenticated": True,
                "user_name": self.authenticated_user.get("user_name"),
            })
        return web.json_response({"authenticated": False})

    async def handle_callback(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        device_id = body.get("deviceId") or body.get("device_id") or "web:auto"
        refresh_token = body.get("refreshToken") or body.get("refresh_token")

        if not refresh_token:
            return web.json_response({"error": "Missing refreshToken in payload"}, status=400)

        print("\n" + "=" * 60)
        print("📥 Received credentials from browser!")
        print(f"Device ID: {device_id}")
        print(f"Refresh Token: {refresh_token[:30]}...")

        # Validate with Jow API
        async with aiohttp.ClientSession() as session:
            client = JowApiClient(session, device_id=device_id, refresh_token=refresh_token)
            try:
                print("🔄 Validating credentials with api.jow.fr...")
                await client.async_refresh_access_token()
                profile = await client.async_get_profile()
                letscook = await client.async_get_letscook()
            except Exception as err:
                print(f"❌ Validation failed: {err}")
                return web.json_response({"error": f"Jow API error: {err}"}, status=401)

        user_name = (
            profile.get("jowProfile", {}).get("firstName")
            or profile.get("jowProfile", {}).get("email")
            or "Jow User"
        )
        email = profile.get("jowProfile", {}).get("email", "N/A")
        provider = profile.get("jowProfile", {}).get("provider", "None")

        collections = letscook.get("collections", {}).get("collections", [])
        shared = letscook.get("sharedRecipes", {}).get("meals", [])

        print("✅ SUCCESS! Logged in successfully.")
        print(f"👤 User: {user_name} ({email})")
        print(f"🛒 Connected Supermarket Provider: {provider}")
        print(f"📚 Collections: {len(collections)}")
        print(f"🍲 Shared Recipes: {len(shared)}")
        print("=" * 60 + "\n")

        self.authenticated_user = {
            "device_id": device_id,
            "refresh_token": refresh_token,
            "user_name": user_name,
            "email": email,
        }

        # Save credentials for future use
        creds_file = os.path.join(os.path.dirname(__file__), "test_credentials.json")
        with open(creds_file, "w", encoding="utf-8") as f:
            json.dump(self.authenticated_user, f, indent=2)
        print(f"💾 Saved test credentials to: {creds_file}")

        self.auth_event.set()

        return web.json_response(
            {"success": True, "user_name": user_name},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, HOST, PORT)
        await self.site.start()

        login_url = f"http://{HOST}:{PORT}/api/jow/login"
        print(f"\n🚀 Jow Web Login Test Server started at: {login_url}")
        print("🌐 Opening your default browser...\n")
        webbrowser.open(login_url)

        print("⏳ Waiting for login from browser (press Ctrl+C to cancel)...")
        try:
            await self.auth_event.wait()
            # Wait 3 seconds so the browser can receive the success status
            await asyncio.sleep(3)
        finally:
            await self.runner.cleanup()
            print("🛑 Server stopped.")


if __name__ == "__main__":
    server = TestLoginServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nCancelled by user.")
