"""Button platform for AlpicAir Heatpump: power toggle + error reset."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_ERROR_RESET


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AlpicAirHeatpumpPowerToggleButton(coordinator, entry),
            AlpicAirHeatpumpResetErrorButton(coordinator, entry),
        ]
    )


class _Base(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="AlpicAir",
            model="Heat Pump Water Heater",
        )


class AlpicAirHeatpumpPowerToggleButton(_Base):
    _attr_icon = "mdi:power"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_power_toggle"
        self._attr_name = "Включить/Выключить"

    async def async_press(self) -> None:
        await self.coordinator.async_toggle_power()


class AlpicAirHeatpumpResetErrorButton(_Base):
    _attr_icon = "mdi:restart-alert"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_reset_error"
        self._attr_name = "Сбросить ошибку"

    async def async_press(self) -> None:
        await self.coordinator.async_write_register(REG_ERROR_RESET, 1)
