import asyncio
import logging
from datetime import timedelta
from typing import Any
from aiohttp import CookieJar
from pyjtechdigital import JtechClient, JtechAuthError, JtechConnectionError

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN, ATTR_MANUFACTURER, ERROR_CONNECT_FAILED, ERROR_FETCH_DATA_FAILED, ERROR_AUTH_FAILED, ERROR_UNKNOWN

from .structures import JtechOutputInfo, JtechSourceInfo

_LOGGER = logging.getLogger(__name__)

class JtechCoordinator(DataUpdateCoordinator):
    """Class to manage fetching and storing J-Tech Digital HDMI Matrix data."""

    def __init__(self, hass, host, username, password):
        """Initialize the data coordinator."""
        self.hass = hass
        self.host = host
        self.username = username
        self.password = password
        self._client = None
        self.connected = False

        self.outputs = []
        self.sources = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=10))

    async def _async_update_data(self):
        """Fetch the latest data from the J-Tech Digital HDMI Matrix."""
        # Implementing the update logic from both versions here
        await self._client_ensure()

        try:
            # TODO: dont rely on all requests, some can fail, its ok for the whole update

            statuses = await self._fetch_status()

            _LOGGER.debug("fetch_statuses", statuses)

            #edid_status = statuses["edid"]

            self.outputs = self._handle_output_update(statuses)
            self.sources = self._handle_source_update(statuses)

            # Return the combined_data with only the required information

            combined_data = { }

            status = statuses["status"]
            if status:
                combined_data["power"] = status.power
                combined_data["model"] = status.model
                combined_data["version"] = status.version

            network_status = statuses["network"]
            if network_status:
                combined_data["hostname"] = network_status.hostname
                combined_data["ipaddress"] = network_status.ipaddress
                combined_data["subnet"] = network_status.subnet
                combined_data["gateway"] = network_status.gateway
                combined_data["macaddress"] = network_status.macaddress
                combined_data["dhcp"] = network_status.dhcp
                combined_data["telnetport"] = network_status.telnetport
                combined_data["tcpport"] = network_status.tcpport

            system_status = statuses["system"]
            if system_status:
                combined_data["baudrate_index"] = system_status.baudrate_index
                combined_data["beep"] = system_status.beep
                combined_data["lock"] = system_status.lock
                combined_data["mode"] = system_status.mode

            web_details = statuses["web_details"]
            if web_details:
                combined_data["title"] = web_details.title

            return combined_data
        except JtechAuthError as err:
            self.connected = False
            raise UpdateFailed(ERROR_AUTH_FAILED, err)
        except Exception as err:
            self.connected = False
            raise UpdateFailed(ERROR_FETCH_DATA_FAILED, err)

    def _handle_source_update(self, statuses):
        output_status = statuses["output"]
        source_status = statuses["source"]
        cec_status = statuses["cec"]
            # Split the source data
        if source_status and source_status.source_names:
            sources_data = []
            for idx, source_name in enumerate(source_status.source_names):
                active = source_status.active_sources[idx]
                edid_index = source_status.edid_indexes[idx]
                cec_selected = idx in cec_status.selected_cec_sources
                outputs = []
                for output_idx, source in enumerate(output_status.selected_sources):
                    if source == idx:
                        outputs.append(output_idx + 1)
                sources_data.append(JtechSourceInfo(outputs, source_name, active, edid_index, cec_selected))
            return sources_data

    def _handle_output_update(self, statuses):
        output_status = statuses["output"]
        cec_status = statuses["cec"]
            # Split the output data
        if output_status and output_status.output_names:
            outputs_data = []
            for idx, output_name in enumerate(output_status.output_names):
                source_idx = output_status.selected_sources[idx]
                cat_name = output_status.output_cat_names[idx]
                connected = output_status.connected_outputs[idx]
                cat_connected = output_status.connected_cat_outputs[idx]
                enabled = output_status.enabled_outputs[idx]
                cat_enabled = output_status.enabled_cat_outputs[idx]
                scaler = output_status.selected_output_scalers[idx]
                cec_selected = idx in cec_status.selected_cec_outputs
                outputs_data.append(JtechOutputInfo(source_idx, output_name, cat_name, connected, cat_connected, enabled, cat_enabled, scaler, cec_selected))
            return outputs_data

    async def _client_connect(self):
        if not self.connected:
            try:
                await self._client.connect(self.username, self.password)
                self.connected = True
            except JtechAuthError as err:
                self.connected = False
                raise ConfigEntryAuthFailed(ERROR_AUTH_FAILED, err) from err
            except JtechConnectionError as err:
                self.connected = False
                raise UpdateFailed(ERROR_CONNECT_FAILED, err) from err
            except Exception as err:
                self.connected = False
                raise UpdateFailed(ERROR_UNKNOWN, err) from err

    async def _client_ensure(self):
        if not self._client:
            session = async_create_clientsession(self.hass, cookie_jar=CookieJar(unsafe=True, quote_cookie=False))
            self._client = JtechClient(self.host, session)

        await self._client_connect()

    async def _fetch_status(self):
        tasks = [
            self._client.get_status(),
            self._client.get_source_status(),
            self._client.get_output_status(),
            self._client.get_cec_status(),
            self._client.get_network(),
            self._client.get_system_status(),
            self._client.get_web_details(),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)  # continue even if there is an exception

        return dict(zip(
            [
                "status",
                "source",
                "output",
                "cec",
                "network",
                "system",
                "web_details",
            ],
            [response if not isinstance(response, Exception) else None for response in responses] # filter out exceptions
        ))

    async def async_enable_output(self, output: int) -> bool:
        """Enable the output with the specified index."""
        return await self._client.set_output_stream(output, True)
    
    async def async_enable_cat_output(self, output: int) -> bool:
        """Enable the cat output with the specified index."""
        return await self._client.set_output_cat_stream(output, True)

    async def async_disable_output(self, output: int) -> bool:
        """Disable the output with the specified index."""
        return await self._client.set_output_stream(output, False)
    
    async def async_disable_cat_output(self, output: int) -> bool:
        """Disable the cat output with the specified index."""
        return await self._client.set_output_cat_stream(output, False)

    async def async_select_source(self, output: int, source: int) -> bool:
        """Select the input source for the specified output."""
        return await self._client.set_video_source(output, source)

    async def async_send_cec_output(self, output: int, command: int) -> bool:
        """Send a CEC command to the specified output."""
        return await self._client.send_cec_output(output, command)

    async def async_send_cec_source(self, source: int, command: int) -> bool:
        """Send a CEC command to the specified source."""
        return await self._client.send_cec_source(source, command)
    
    async def async_power_on(self) -> bool:
        return await self._client.set_power(True)
    
    async def async_power_off(self) -> bool:
        return await self._client.set_power(False)
