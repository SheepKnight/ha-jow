"""Direct test script for JowApiClient using async aiohttp."""

import asyncio
import importlib.util
import os
import sys
import types
import aiohttp

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Mock const for standalone run
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

DEVICE_ID = "web:c1bc9317bacb61c14c164cf80c452dca"
REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJwcm9kIiwidHlwZSI6InJlZnJlc2giLCJ1c2VySWQiOiI2OTdmNGZlY2FiNGY2NTYzNTA1YjQ5ZjIiLCJzYWx0IjoiU2kyN09aUy9CMU5tYm9NVVQ0bW9pZz09IiwicHJvdmlkZXIiOiJjaHJvbm9kcml2ZSIsImRpdmlzaW9uIjoibWFpbiIsImRldmljZUlkIjoid2ViOmMxYmM5MzE3YmFjYjYxYzE0YzE2NGNmODBjNDUyZGNhIiwiYXZhaWxhYmlsaXR5Wm9uZUlkIjoiRlIiLCJzdWJzY3JpcHRpb24iOnsiaXNTdWJzY3JpcHRpb25SZXF1aXJlZCI6ZmFsc2V9LCJpYXQiOjE3OTEyMjUxNDYsImV4cCI6MTgwNjc3NzE0NiwiYXVkIjoiam93dXNlcnMiLCJpc3MiOiJhcGkiLCJqdGkiOiIxcmtpQlE5dm1ZT3VQRzNaMVUzRUZnPT0ifQ.r6eUf3xyn6JesQLNmz4nh-qL_GsLPuZ1vtg68vAM7LE"


async def main():
    print("Testing JowApiClient async flow...")
    async with aiohttp.ClientSession() as session:
        client = JowApiClient(session, device_id=DEVICE_ID, refresh_token=REFRESH_TOKEN)

        print("1. Refreshing Access Token...")
        token = await client.async_refresh_access_token()
        print(f"   Token obtained: {token[:30]}...")

        print("\n2. Fetching Unified Profile...")
        profile = await client.async_get_profile()
        p = profile.get("jowProfile", {})
        print(f"   Name: {p.get('firstName')} {p.get('lastName')}")
        print(f"   Email: {p.get('email')}")
        print(f"   Provider: {p.get('provider')}")

        print("\n3. Fetching Let's Cook Data...")
        data = await client.async_get_letscook(preferred_limit=5)
        cols = data.get("collections", {}).get("collections", [])
        shared = data.get("sharedRecipes", {}).get("meals", [])
        print(f"   Collections ({len(cols)}):")
        for c in cols:
            print(f"     • {c.get('title')} ({c.get('type')})")
        print(f"   Shared recipes sample ({len(shared)}):")
        for m in shared[:3]:
            r = m.get("recipe", {})
            print(f"     • {r.get('title')} ({m.get('coversCount')} covers)")

    print("\nAll API calls succeeded!")


if __name__ == "__main__":
    asyncio.run(main())
