"""Remote control support for J-Tech Digital HDMI Matrix."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import JtechEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up J-Tech Digital HDMI Matrix Remote from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unique_id = config_entry.unique_id
    assert unique_id is not None

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        JtechRemote(coordinator, f"{unique_id}_{output}", coordinator.model, coordinator.output_cat_names[output-1], output)
            for output in range(1, coordinator.outputs_count+1),
    )


class JtechRemote(JtechEntity, RemoteEntity):
    """Representation of a J-Tech Digital HDMI Matrix Remote."""

    _attr_name = None

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        info = self._output_info()

        return self.coordinator.power and ((info["connected"] and info["enabled"]) or (info["connected_cat"] and info["enabled_cat"]))

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to device."""
        repeats = kwargs[ATTR_NUM_REPEATS]
        #await self.coordinator.async_send_command(command, repeats)