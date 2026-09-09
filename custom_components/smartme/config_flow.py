"""Config flow for the Smart-me integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SmartMeApiClient, SmartMeApiError, SmartMeAuthError
from .const import CONF_DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SmartMeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for smart-me."""

    VERSION = 1

    def __init__(self) -> None:
        self._username: str | None = None
        self._password: str | None = None
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask for the smart-me account credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = SmartMeApiClient(
                session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            try:
                self._devices = await client.async_get_devices()
            except SmartMeAuthError:
                errors["base"] = "invalid_auth"
            except SmartMeApiError:
                _LOGGER.exception("Error connecting to the smart-me API")
                errors["base"] = "cannot_connect"
            else:
                if not self._devices:
                    errors["base"] = "no_devices"
                else:
                    await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                    self._abort_if_unique_id_configured()
                    self._username = user_input[CONF_USERNAME]
                    self._password = user_input[CONF_PASSWORD]
                    return await self.async_step_devices()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user pick which smart-me devices to add."""
        device_options = {
            device["id"]: f"{device.get('name') or 'Unbenannt'} ({device.get('serial', '?')})"
            for device in self._devices
        }

        if user_input is not None:
            return self.async_create_entry(
                title=self._username or "Smart-me",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                },
                options={CONF_DEVICES: user_input[CONF_DEVICES]},
            )

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICES, default=list(device_options)
                    ): cv.multi_select(device_options),
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Allow changing the selected devices later on."""
        return SmartMeOptionsFlow()


class SmartMeOptionsFlow(config_entries.OptionsFlow):
    """Handle changing which devices are enabled after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Re-fetch the device list and let the user adjust the selection."""
        errors: dict[str, str] = {}

        session = async_get_clientsession(self.hass)
        client = SmartMeApiClient(
            session,
            self.config_entry.data[CONF_USERNAME],
            self.config_entry.data[CONF_PASSWORD],
        )

        try:
            devices = await client.async_get_devices()
        except SmartMeApiError:
            errors["base"] = "cannot_connect"
            devices = []

        device_options = {
            device["id"]: f"{device.get('name') or 'Unbenannt'} ({device.get('serial', '?')})"
            for device in devices
        }

        if user_input is not None and not errors:
            return self.async_create_entry(data={CONF_DEVICES: user_input[CONF_DEVICES]})

        current = self.config_entry.options.get(CONF_DEVICES, list(device_options))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICES, default=current
                    ): cv.multi_select(device_options),
                }
            ),
            errors=errors,
        )
