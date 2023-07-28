"""Media player support for J-Tech Digital HDMI Matrix integration."""
from __future__ import annotations
import asyncio
import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_STOP,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_NEXT_TRACK,
    SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_MUTE,
)
from homeassistant.components.homekit.const import (
    EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED,
    KEY_ARROW_DOWN,
    KEY_ARROW_LEFT,
    KEY_ARROW_RIGHT,
    KEY_ARROW_UP,
    KEY_BACK,
    KEY_EXIT,
    KEY_FAST_FORWARD,
    KEY_INFORMATION,
    KEY_NEXT_TRACK,
    KEY_PREVIOUS_TRACK,
    KEY_REWIND,
    KEY_SELECT,
    KEY_PLAY_PAUSE,
    ATTR_KEY_NAME,
)
from homeassistant.const import STATE_OFF, STATE_PLAYING, STATE_IDLE, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_MANUFACTURER,
    CONF_HDMI_STREAM_TOGGLE,
    CONF_CAT_STREAM_TOGGLE,
    CONF_VOLUME_CONTROL,
    CONF_CEC_SOURCE_TOGGLE,
    CONF_CEC_OUTPUT_TOGGLE,
    CONF_CEC_DELAY_POWER, 
    CONF_CEC_DELAY_SOURCE,
)
from .coordinator import JtechCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up J-Tech Digital HDMI Matrix Media Player from a config_entry."""

    # Get the coordinator for this entry
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unique_id = config_entry.unique_id
    assert unique_id is not None

    # Ensure we have the latest data from the coordinator
    await coordinator.async_config_entry_first_refresh()

    # Create media player entities for each output in the HDMI matrix
    entities = [
        JtechMediaPlayer(coordinator, output_idx + 1, unique_id) 
            for output_idx, output_info in enumerate(coordinator.outputs)
    ]

    # Add the media player entities to Home Assistant
    async_add_entities(entities, update_before_add=True)


class JtechMediaPlayer(MediaPlayerEntity):
    """Representation of a J-Tech Digital HDMI Matrix Output as a media player."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:video-input-hdmi"

    def _get_output_info(self):
        """Get the output information for the current output_index."""
        return self._coordinator.outputs[self._output_index - 1]

    def _get_source_info(self):
        """Get the source information for the given output_info."""
        output_info = self._get_output_info()
        if output_info:
            return self._coordinator.sources[output_info.source - 1]
        return None

    def _get_volume_control(self):
        """Get the volume_control option."""
        return self._coordinator.options.get(CONF_VOLUME_CONTROL, "none")

    def _get_hdmi_stream_toggle(self):
        """Get the hdmi_stream_toggle option."""
        _LOGGER.debug("get_hdmi_stream_toggle", self._coordinator.options)
        return self._coordinator.options.get(CONF_HDMI_STREAM_TOGGLE, False)

    def _get_cat_stream_toggle(self):
        """Get the cat_stream_toggle option."""
        return self._coordinator.options.get(CONF_CAT_STREAM_TOGGLE, False)
    
    def _get_cec_delay_power(self):
        """Get the cec_delay_power option."""
        return self._coordinator.options.get(CONF_CEC_DELAY_POWER, 0)
    
    def _get_cec_delay_source(self):
        """Get the cec_delay_source option."""
        return self._coordinator.options.get(CONF_CEC_DELAY_SOURCE, 0)

    def _get_cec_source_toggle(self):
        """Get the cec_source_toggle option."""
        return self._coordinator.options.get(CONF_CEC_SOURCE_TOGGLE, False)
    
    def _get_cec_output_toggle(self):
        """Get the cec_output_toggle option."""
        return self._coordinator.options.get(CONF_CEC_OUTPUT_TOGGLE, False)

    def __init__(self, coordinator: JtechCoordinator, output_index: int, unique_id_entry: str):
        """Initialize the media player."""
        self._coordinator = coordinator
        self._output_index = output_index
        self._unique_id_entry = unique_id_entry

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        supported_features = (
            SUPPORT_SELECT_SOURCE
            | SUPPORT_PLAY_MEDIA
            | SUPPORT_PAUSE
            | SUPPORT_PLAY
            | SUPPORT_STOP
            | SUPPORT_PREVIOUS_TRACK
            | SUPPORT_NEXT_TRACK
        )

        # Add volume controls if available
        volume_control = self._get_volume_control()
        if volume_control and volume_control != "none":
            supported_features |= SUPPORT_VOLUME_STEP
            supported_features |= SUPPORT_VOLUME_MUTE

        # Add turn on/off controls if HDMI and CAT switches are not available
        toggle_hdmi = self._get_hdmi_stream_toggle()
        toggle_cat = self._get_cat_stream_toggle()
        if not (toggle_hdmi and toggle_cat):
            supported_features |= SUPPORT_TURN_ON
            supported_features |= SUPPORT_TURN_OFF

        return supported_features

    @property
    def unique_id(self):
        """Return a unique ID for the media player."""
        return f"{self._unique_id_entry}_output_{self._output_index}"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        output_info = self._get_output_info()

        return DeviceInfo(
            identifiers={ (DOMAIN, self.unique_id) },
            default_name=output_info.name if output_info else f"Output {self._output_index}",
            manufacturer=ATTR_MANUFACTURER,
            model=self._coordinator.data["model"],
            sw_version=self._coordinator.data["version"],
            via_device=(DOMAIN, self._unique_id_entry),
            configuration_url=f"http://{self._coordinator.data['hostname']}" if self._coordinator.data["hostname"] else None
        )

    @property
    def device_class(self):
        """Return the device class."""
        return MediaPlayerDeviceClass.TV

    # TODO: handle power of coordinator

    @property
    def state(self):
        """Return the state of the media player."""
        output_info = self._get_output_info()
        if output_info:
            source_info = self._get_source_info()
            
            hdmi_stream_toggle = self._get_hdmi_stream_toggle()
            cat_stream_toggle = self._get_cat_stream_toggle()

            if cat_stream_toggle and hdmi_stream_toggle:
                if not (output_info.cat_connected and output_info.cat_enabled and output_info.connected and output_info.enabled):
                    return STATE_OFF
                if source_info and source_info.cat_active and source_info.active:
                    return STATE_PLAYING

            if cat_stream_toggle:
                if not (output_info.cat_connected and output_info.cat_enabled):
                    return STATE_OFF
                if source_info and source_info.cat_active:
                    return STATE_PLAYING
                
            if hdmi_stream_toggle:
                if not (output_info.connected and output_info.enabled):
                    return STATE_OFF
                if source_info and source_info.active:
                    return STATE_PLAYING

            return STATE_IDLE

        # Output information not available, assume the state is unavailable
        return STATE_UNAVAILABLE

    @property
    def source_list(self):
        """Return the list of available input sources."""
        return [source.name for source in  self._coordinator.sources]

    @property
    def source(self):
        """Return the current input source."""
        output_info = self._get_output_info()
        if output_info:
            source_info = self._get_source_info()
            if source_info:
                return source_info.name
        return None

    async def async_select_source(self, source):
        """Select input source."""
        for source_idx, source_info in enumerate(self._coordinator.sources):
            if source_info.name == source:
                await self._coordinator.async_select_source(self._output_index, source_idx + 1)
                break

    async def async_turn_on(self):
        """Enable the output and send necessary CEC commands to turn on the connected devices."""
        hdmi_stream_toggle = self._get_hdmi_stream_toggle()
        cat_stream_toggle = self._get_cat_stream_toggle()
        if hdmi_stream_toggle:
            await self._coordinator.async_enable_output(self._output_index)
        if cat_stream_toggle:
            await self._coordinator.async_enable_cat_output(self._output_index)

        cec_source_toggle = self._get_cec_source_toggle()
        cec_output_toggle = self._get_cec_output_toggle()
        if (cec_source_toggle or cec_output_toggle) and (hdmi_stream_toggle or cat_stream_toggle):
            delay_power = self._get_cec_delay_power()
            if delay_power and delay_power > 0:
                await asyncio.sleep(delay_power)
        if cec_output_toggle:
            await self._async_send_cec_source(1) # turn on selected source
        if cec_output_toggle:
            await self._coordinator.async_send_cec_output(self._output_index, 0) # turn on hdmi monitor
        
        if cec_output_toggle:
            delay_source = self._get_cec_delay_source()
            if delay_source and delay_source > 0:
                await asyncio.sleep(delay_source)
            await self._coordinator.async_send_cec_output(self._output_index, 5)

    async def async_turn_off(self):
        """Disable the output."""
        cec_source_toggle = self._get_cec_source_toggle()
        cec_output_toggle = self._get_cec_output_toggle()
        if cec_output_toggle:
            await self._coordinator.async_send_cec_output(self._output_index, 1)
        if cec_source_toggle:
            await self._async_send_cec_source(2) # turn off selected source
        if cec_source_toggle or cec_output_toggle:
            delay_power = self._get_cec_delay_power()
            if delay_power and delay_power > 0:
                await asyncio.sleep(self._get_cec_delay_power())

        hdmi_stream_toggle = self._get_hdmi_stream_toggle()
        cat_stream_toggle = self._get_cat_stream_toggle()
        if hdmi_stream_toggle:
            await self._coordinator.async_disable_output(self._output_index)
        if cat_stream_toggle:
            await self._coordinator.async_disable_cat_output(self._output_index)
        

    async def async_volume_up(self):
        """Send CEC command to increase volume."""
        await self._async_volume_send(4, 19)

    async def async_volume_down(self):
        """Send CEC command to decrease volume."""
        await self._async_volume_send(3, 18)

    async def async_volume_mute(self):
        """Send CEC command to mute volume."""
        await self._async_volume_send(2, 17)

    async def _async_volume_send(self, output_command, source_command):
        volume_control = self._get_volume_control()

        if volume_control == "output":
            await self._coordinator.async_send_cec_output(self._output_index, output_command)
        elif volume_control == "source":
            await self._async_send_cec_source(source_command)

    async def _async_send_cec_source(self, source_command):
        output_info = self._get_output_info()
        if output_info:
            await self._coordinator.async_send_cec_source(output_info.source, source_command)

    async def async_media_previous_track(self):
        """Send CEC command for previous track."""
        await self._async_send_cec_source(10)

    async def async_media_next_track(self):
        """Send CEC command for next track."""
        await self._async_send_cec_source(12)

    async def async_media_play(self):
        """Send CEC command to play."""
        await self._async_send_cec_source(11)

    async def async_media_stop(self):
        """Send CEC command to stop."""
        await self._async_send_cec_source(16)

    async def async_media_pause(self):
        """Send CEC command to pause."""
        await self._async_send_cec_source(14)

    async def _handle_tv_remote_key_press(self, event):
        """Handle HomeKit TV remote key presses."""
        remote_id = event.data.get("unique_id")
        key_name = event.data.get(ATTR_KEY_NAME)

        _LOGGER.debug("homekit_tv_remote_key_pressed", event, event.data)

        if remote_id == self.unique_id:
            key_name_mapping = {
                KEY_ARROW_UP: 3,
                KEY_ARROW_LEFT: 4,
                KEY_ARROW_RIGHT: 6,
                KEY_ARROW_DOWN: 8,
                KEY_SELECT: 5,
                KEY_INFORMATION: 7,
                KEY_BACK: 9,
                KEY_REWIND: 13,
                KEY_FAST_FORWARD: 15,
            }
            cec_command = key_name_mapping.get(key_name)
            if cec_command:
                # Send the CEC command
                self._async_send_cec_source(cec_command)

    async def async_added_to_hass(self):
        """Subscribe to updates and handle HomeKit TV remote key presses."""
        self.hass.bus.async_listen(EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, self._handle_tv_remote_key_press)

    @callback
    async def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Trigger an entity state update to reflect the latest data from the coordinator
        _LOGGER.debug("handle_coordinator_update_data", self._coordinator.data)
        self.async_write_ha_state()
