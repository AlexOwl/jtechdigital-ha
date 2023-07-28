"""Update coordinator for J-Tech Digital HDMI Matrix integration."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine, Iterable
from datetime import timedelta
from functools import wraps
import logging
from types import MappingProxyType
from typing import Any, Concatenate, Final, ParamSpec, TypeVar

from pyjtechdigital import JtechClient, JtechError, JtechAuthError, JtechConnectionError, JtechConnectionTimeout, JtechInvalidSource, JtechInvalidOutput, JtechOptionError

from homeassistant.components.media_player import MediaType
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN
from .helpers import JtechOutputInfo, JtechSourceInfo

_JtechCoordinatorT = TypeVar("_JtechCoordinatorT", bound="JtechCoordinator")
_P = ParamSpec("_P")
_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL: Final = timedelta(seconds=10)

def catch_jtechdigital_errors(
    func: Callable[Concatenate[_JtechCoordinatorT, _P], Awaitable[None]]
) -> Callable[Concatenate[_JtechCoordinatorT, _P], Coroutine[Any, Any, None]]:
    """Catch J-Tech Digital errors."""

    @wraps(func)
    async def wrapper(
        self: _JtechCoordinatorT,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        """Catch J-Tech Digital errors and log message."""
        try:
            await func(self, *args, **kwargs)
        except JtechError as err:
            _LOGGER.error("Command error: %s", err)
        await self.async_request_refresh()

    return wrapper


class JtechCoordinator(DataUpdateCoordinator[None]):
    """Representation of a J-Tech Digital Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: JtechClient,
        config: MappingProxyType[str, Any],
    ) -> None:
        """Initialize J-Tech Digital Client."""

        self.client = client
        self.user = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]

        self.power: bool | None = None
        self.model: str | None = None
        self.mac: str | None = None
        self.version: str | None = None
        self.baudrate_index: int | None = None
        self.beep: bool | None = None
        self.lock: bool | None = None
        self.mode: int | None = None

        self.presets_names: list[str] = []

        self.sources_names: list[str] = []
        self.sources_active: list[bool] = []
        self.sources_edids: list[int] = []
        self.sources_cec_selected: list[int] = []

        self.outputs_names: list[str] = []
        self.outputs_cat_names: list[str] = []
        self.outputs_connected: list[bool] = []
        self.outputs_cat_connected: list[bool] = []
        self.outputs_enabled: list[bool] = []
        self.outputs_cat_enabled: list[bool] = []
        self.outputs_sources: list[int] = []
        self.outputs_scalers: list[int] = []
        self.outputs_cec_selected: list[int] = []

        self.connected = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=1.0, immediate=False
            ),
        )

    async def _async_update_data(self) -> None:
        """Connect and fetch data."""
        try:
            if not self.connected:
                try:
                    await self.client.connect(
                        user=self.user,
                        password=self.password,
                    )   
                    self.connected = True
                except JtechAuthError as err:
                    raise ConfigEntryAuthFailed from err
                
                self.sources_count = self.client._sources_count
                self.outputs_count = self.client._outputs_count
                await self.async_update_status()

            await self.async_update_video_status()
            await self.async_update_source_status()
            await self.async_update_output_status()
            await self.async_update_system_status()
        except (JtechConnectionError, JtechConnectionTimeout):
            self.power = False
            self.connected = False
            _LOGGER.debug("Update skipped, J-Tech Digital is off")
        except err:
            self.power = False
            self.connected = False
            raise UpdateFailed("Error communicating with device") from err

    async def async_update_status(self) -> None:
        """Update status information."""
        status = await self.client.get_status()
        self.power = status.power
        if status.model:
            self.model = status.model
        if status.macaddress:
            self.mac = status.macaddress
        if status.version:
            self.version = status.version

    async def async_update_video_status(self) -> None:
        """Update video status information."""
        video_status = await self.client.get_video_status()
        self.power = video_status.power
        self.outputs_sources = video_status.selected_sources
        self.preset_names = video_status.preset_names

        if video_status.source_names:
            self.sources_names = video_status.source_names
        if video_status.output_names:
            self.outputs_names = video_status.output_names
        if video_status.output_cat_names:
            self.outputs_cat_names = video_status.output_cat_names

    async def async_update_output_status(self) -> None:
        """Update output status information."""
        output_status = await self.client.get_output_status()
        self.power = output_status.power
        self.outputs_sources = output_status.selected_sources
        self.outputs_scalers = output_status.selected_output_scalers
        self.outputs_enabled = output_status.enabled_outputs
        self.outputs_cat_enabled = output_status.enabled_cat_outputs
        self.outputs_connected = output_status.connected_outputs
        self.outputs_cat_connected = output_status.connected_cat_outputs

        if output_status.output_names:
            self.outputs_names = output_status.output_names
        if output_status.output_cat_names:
            self.outputs_cat_names = output_status.output_cat_names

    async def async_update_source_status(self) -> None:
        """Update source status information."""
        source_status = await self.client.get_source_status()
        self.power = source_status.power
        self.sources_edids = source_status.edid_indexes
        self.sources_active = source_status.active_sources

        if source_status.source_names:
            self.sources_names = source_status.source_names

    async def async_update_cec_status(self) -> None:
        """Update cec status information."""
        cec_status = await self.client.get_cec_status()

        self.sources_cec_selected = cec_status.selected_cec_sources
        self.outputs_cec_selected = cec_status.selected_cec_outputs

        if cec_status.source_names:
            self.sources_names = cec_status.source_names
        if cec_status.alloutputname:
            self.outputs_names = cec_status.output_names

    async def async_update_network(self) -> None:
        """Update network information."""
        network = await self.client.get_network()
        self.power = network.power
        self.model = network.model
        self.mac = network.macaddress

    async def async_update_system_status(self) -> None:
        """Update system status information."""
        system_status = await self.client.get_system_status()
        self.power = system_status.power
        self.baudrate_index = system_status.baudrate_index
        self.beep = system_status.beep
        self.lock = system_status.lock
        self.mode = system_status.mode

        if system_status.version:
            self.version = system_status.version


    @catch_jtechdigital_errors
    async def async_turn_on(self) -> None:
        """Turn the device on."""
        await self.client.set_power(True)

    @catch_jtechdigital_errors
    async def async_turn_off(self) -> None:
        """Turn the device off."""
        await self.client.set_power(False)

    @catch_jtechdigital_errors
    async def async_reboot_device(self) -> None:
        """Send command to reboot the device."""
        await self.client.reboot()

    def get_output_info(self, output: int) -> dict[str, Any]:
        self.client.validate_output(output)
        output_arr_index = output - 1

        return JtechOutputInfo(
            self.outputs_sources[output_arr_index],
            self.outputs_names[output_arr_index],
            self.outputs_cat_names[output_arr_index],
            self.outputs_connected[output_arr_index],
            self.outputs_cat_connected[output_arr_index],
            self.outputs_enabled[output_arr_index],
            self.outputs_cat_enabled[outoutput_arr_indexput],
            self.outputs_scalers[output_arr_index],
            output in self.outputs_cec_selected,
        )

    def get_source_info(self, source: int) -> dict[str, Any]:
        self.client.validate_source(source)
        source_arr_index = source - 1

        outputs = []
        for _output, _source in enumerate(self.outputs_sources):
            if _source == source:
                outputs.append(_output)

        return JtechSourceInfo(
            outputs,
            self.sources_names[source_arr_index],
            self.sources_active[source_arr_index],
            self.sources_edids[source_arr_index],
            source in self.sources_cec_selected,
        )


    @catch_jtechdigital_errors
    async def async_output_turn_on(self, output: int) -> None:
        """Turn the output on."""
        await self.client.set_output_stream(output, True)
        await self.client.set_output_cat_stream(output, True)

    @catch_jtechdigital_errors
    async def async_output_turn_off(self, output: int) -> None:
        """Turn the output off."""
        await self.client.set_output_stream(output, False)
        await self.client.set_output_cat_stream(output, False)
    
    @catch_jtechdigital_errors
    async def async_output_set_source(self, output: int, source: int,) -> None:
        await self.client.set_video_source(output, source)

