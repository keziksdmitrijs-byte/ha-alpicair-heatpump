"""Select platform for AlpicAir Heatpump: operating mode dropdown."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_MAP, MODE_LABELS_RU

OPTIONS = list(MODE_LABELS_RU.values())
LABEL_TO_KEY = {v: k for k, v in MODE_LABELS_RU.items()}
KEY_TO_REGISTER = {v: k for k, v in MODE_MAP.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlpicAirHeatpumpModeSelect(coordinator, entry)])


class AlpicAirHeatpumpModeSelect(CoordinatorEntity, SelectEntity):
    _attr_icon = "mdi:heat-pump"
    _attr_options = OPTIONS

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_mode_select"
        self._attr_name = "Режим работы"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="AlpicAir",
            model="Heat Pump Water Heater",
        )

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("mode")
        key = MODE_MAP.get(raw)
        return MODE_LABELS_RU.get(key)

    async def async_select_option(self, option: str) -> None:
        key = LABEL_TO_KEY[option]
        value = KEY_TO_REGISTER[key]
        await self.coordinator.async_write_mode(value)
