"""Thin async client for the smart-me REST API."""

from __future__ import annotations

import aiohttp

from .const import API_BASE_URL


class SmartMeApiError(Exception):
    """Raised for any error while talking to the smart-me API."""


class SmartMeAuthError(SmartMeApiError):
    """Raised when the smart-me API rejects the credentials."""


def _normalize(device: dict) -> dict:
    """Normalize smart-me's PascalCase JSON keys (e.g. "Id") to camelCase
    (e.g. "id"), which is what the OpenAPI schema documents and what the
    rest of this integration is written against.
    """
    return {(key[:1].lower() + key[1:]): value for key, value in device.items()}


class SmartMeApiClient:
    """Wrapper around the smart-me `/Devices` endpoints (Basic Auth)."""

    def __init__(
        self, session: aiohttp.ClientSession, username: str, password: str
    ) -> None:
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password)

    async def async_get_devices(self) -> list[dict]:
        """Return all devices visible to this account."""
        devices = await self._request("/Devices")
        return [_normalize(device) for device in devices]

    async def async_get_device(self, device_id: str) -> dict:
        """Return a single device by its ID."""
        device = await self._request(f"/Devices/{device_id}")
        return _normalize(device)

    async def _request(self, path: str):
        try:
            async with self._session.get(
                f"{API_BASE_URL}{path}",
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status == 401:
                    raise SmartMeAuthError("Invalid username or password")
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SmartMeApiError(str(err)) from err
