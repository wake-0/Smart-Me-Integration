"""Data update coordinator for the Smart-me integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartMeApiClient, SmartMeApiError, SmartMeAuthError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SmartMeCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Polls the smart-me API for the selected devices.

    Keyed by device ID so entities can look up their own device's data
    without re-fetching it individually.
    """

    def __init__(
        self, hass: HomeAssistant, client: SmartMeApiClient, device_ids: list[str]
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="smartme",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._client = client
        self._device_ids = device_ids

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            return {
                device_id: await self._client.async_get_device(device_id)
                for device_id in self._device_ids
            }
        except SmartMeAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except SmartMeApiError as err:
            raise UpdateFailed(f"Error communicating with smart-me API: {err}") from err
