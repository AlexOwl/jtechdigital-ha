"""Config flow to configure the J-Tech Digital HDMI Matrix integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiohttp import CookieJar
from pyjtechdigital import JtechClient, JtechError, JtechAuthError, JtechNotSupported
import voluptuous as vol

from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util.network import is_host_valid

from .const import (
    DOMAIN,
    CONF_HDMI_STREAM_TOGGLE,
    CONF_CAT_STREAM_TOGGLE,
    CONF_CEC_SOURCE_TOGGLE,
    CONF_CEC_OUTPUT_TOGGLE,
    CONF_CEC_DELAY_POWER,
    CONF_CEC_DELAY_SOURCE,
    CONF_CEC_VOLUME_CONTROL,
)

class JtechConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for J-Tech Digital HDMI Matrix integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.entry: ConfigEntry | None = None

        self._data: dict[str, Any] = {}
        self._client: JtechClient | None = None



    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        schema = {
            vol.Required(CONF_HOST): str 
        }
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            if is_host_valid(host):
                self._data[CONF_HOST] = host
                return await self.async_step_authorize()

            errors[CONF_HOST] = "invalid_host"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle authorize step."""
        schema = {
            vol.Required(CONF_USERNAME, default="Admin"): str,
            vol.Required(CONF_PASSWORD): str,
        }
        errors: dict[str, str] = {}

        self._create_client()

        if user_input is not None:
            self._data[CONF_USERNAME] = user_input[CONF_USERNAME]
            self._data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            
            try:
                await self._async_client_connect()
            except JtechAuthError:
                errors["base"] = "invalid_auth"
            except JtechNotSupported:
                errors["base"] = "unsupported_model"
            except JtechError:
                errors["base"] = "cannot_connect"
            else:
                if self.entry:
                    return await self._async_update_entry()
                else :
                    return await self._async_create_entry()
        elif not self.entry:
            try:
                self._data[CONF_USERNAME] = "User"
                self._data[CONF_PASSWORD] = "user"
                await self._async_client_connect()

                schema = {
                    vol.Required(CONF_USERNAME, default=self._data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=self._data[CONF_PASSWORD]): str,
                }
            except:
                pass

            try:
                self._data[CONF_USERNAME] = "Admin"
                self._data[CONF_PASSWORD] = "admin"
                await self._async_client_connect()

                schema = {
                    vol.Required(CONF_USERNAME, default=self._data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=self._data[CONF_PASSWORD]): str,
                }
            except:
                pass
            

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Handle configuration by re-auth."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        self._data = {**entry_data}
        return await self.async_step_authorize()


    async def _async_create_entry(self) -> FlowResult:
        """Create J-Tech Digital HDMI Matrix device from config."""
        assert self._client
        await self._async_client_connect()

        status = await self._client.get_status()

        unique_id = f"{DOMAIN}_{status.macaddress}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        try:
            web_details = await self._client.get_web_details()
        except:
            web_details = None
        title = web_details.title if web_details else status.hostname

        return self.async_create_entry(
            title=title, 
            data=self._data
        )

    async def _async_update_entry(self) -> FlowResult:
        """Reauthorize J-Tech Digital HDMI Matrix device from config."""
        assert self.entry
        assert self._client
        await self._async_client_connect()

        self.hass.config_entries.async_update_entry(self.entry, data=self._data)
        await self.hass.config_entries.async_reload(self.entry.entry_id)
        return self.async_abort(reason="reauth_successful")


    def _create_client(self) -> None:
        """Create J-Tech Digital HDMI Matrix _client from config."""
        host = self._data[CONF_HOST]
        session = async_create_clientsession(self.hass, cookie_jar=CookieJar(unsafe=True, quote_cookie=False))
        self._client = JtechClient(host=host, session=session)

    async def _async_client_connect(self) -> None:
        """Connect to J-Tech Digital HDMI Matrix device from config."""
        assert self._client

        user = self._data[CONF_USERNAME]
        password = self._data[CONF_PASSWORD]

        await self._client.connect(user, password)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return JtechOptionsFlow(config_entry)
    
# TODO: change options per output

class JtechOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle initial options flow."""
        options = self._config_entry.options

        schema = {
            vol.Optional(CONF_HDMI_STREAM_TOGGLE, default=options.get(CONF_HDMI_STREAM_TOGGLE, True)): bool,
            vol.Optional(CONF_CAT_STREAM_TOGGLE, default=options.get(CONF_CAT_STREAM_TOGGLE, True)): bool,
            vol.Optional(CONF_CEC_DELAY_POWER, default=options.get(CONF_CEC_DELAY_POWER, 2)): int,
            vol.Optional(CONF_CEC_DELAY_SOURCE, default=options.get(CONF_CEC_DELAY_SOURCE, 2)): int,
            vol.Optional(CONF_CEC_SOURCE_TOGGLE, default=options.get(CONF_CEC_SOURCE_TOGGLE, True)): bool,
            vol.Optional(CONF_CEC_OUTPUT_TOGGLE, default=options.get(CONF_CEC_OUTPUT_TOGGLE, False)): bool,
            vol.Optional(CONF_CEC_VOLUME_CONTROL, default=options.get(CONF_CEC_VOLUME_CONTROL, "source")): vol.In(["source", "output", "none"]),
        }
        errors: dict[str, str] = {}

        if user_input is not None:   
            self.hass.async_create_task(self.hass.config_entries.async_reload(self._config_entry.entry_id))
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
        )