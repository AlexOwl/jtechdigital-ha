"""A entity class for J-Tech Digital HDMI Matrix integration."""
from typing import Any

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import JtechCoordinator
from .const import ATTR_MANUFACTURER, DOMAIN


class JtechEntity(CoordinatorEntity[JtechCoordinator]):
    """Jtech entity class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JtechCoordinator,
        unique_id: str,
        model: str,
        name: str,
        output: int,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self._output = output
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer=ATTR_MANUFACTURER,
            model=model,
            name=name,
        )

    def _output_info(self,) -> dict[str, Any]:
        return self.coordinator.get_output_info(self._output)

    async def async_turn_on(self,) -> None:
        await self.coordinator.async_output_turn_on(self._output)

    async def async_turn_off(self,) -> None:
        await self.coordinator.async_output_turn_off(self._output)