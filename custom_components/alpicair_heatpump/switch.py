"""Switch platform for AlpicAir Heatpump: auxiliary boolean state bits."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    BIT_QUIET_MODE,
    BIT_WEATHER_DEPEND,
    BIT_DISINFECTION,
    BIT_FAST_HOT_WATER,
)

SWITCHES = [
    ("quiet_mode", BIT_QUIET_MODE, "Тихий режим", "mdi:volume-mute"),
    ("weather_depend", BIT_WEATHER_DEPEND, "Погодозависимый режим", "mdi:weather-partly-cloudy"),
    ("disinfection", BIT_DISINFECTION, "Дезинфекция бака", "mdi:water-alert"),
    ("fast_hot_water", BIT_FAST_HOT_WATER, "Быстрый нагрев ГВС", "mdi:water-boiler"),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlpicAirHeatpumpBitSwitch(coordinator, entry, k, a, n, i) for k, a, n, i in SWITCHES])


class AlpicAirHeatpumpBitSwitch(CoordinatorEntity, SwitchEntity):
    """Writes a single coil bit via function code 0x0F (Write Multiple Coils, count=1)."""

    def __init__(self, coordinator, entry: ConfigEntry, data_key: str, bit_address: int, name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._data_key = data_key
        self._bit_address = bit_address
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_name = name
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="AlpicAir",
            model="Heat Pump Water Heater",
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get(self._data_key))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_coil_bit(self._bit_address, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_coil_bit(self._bit_address, False)
