"""Number platform for AlpicAir Heatpump: tank setpoint + power limit + water heating temp."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_POWER_LIMIT,
    REG_WOT_HEAT,
    MIN_TANK_TEMP,
    MAX_TANK_TEMP,
    TANK_TEMP_STEP,
    MIN_WOT_HEAT_TEMP,
    MAX_WOT_HEAT_TEMP,
    WOT_HEAT_TEMP_STEP,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AlpicAirHeatpumpTankSetpointNumber(coordinator, entry),
            AlpicAirHeatpumpWotHeatNumber(coordinator, entry),
            AlpicAirHeatpumpPowerLimitNumber(coordinator, entry),
        ]
    )


class _Base(CoordinatorEntity, NumberEntity):
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


class AlpicAirHeatpumpTankSetpointNumber(_Base):
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_native_min_value = MIN_TANK_TEMP
    _attr_native_max_value = MAX_TANK_TEMP
    _attr_native_step = TANK_TEMP_STEP
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:water-thermometer"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tank_setpoint"
        self._attr_name = "Целевая температура бака ГВС"

    @property
    def native_value(self):
        return self.coordinator.data.get("t_water_tank_setpoint")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_tank_setpoint(value)


class AlpicAirHeatpumpWotHeatNumber(_Base):
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_native_min_value = MIN_WOT_HEAT_TEMP
    _attr_native_max_value = MAX_WOT_HEAT_TEMP
    _attr_native_step = WOT_HEAT_TEMP_STEP
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:water-thermometer"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wot_heat"
        self._attr_name = "Температура отопления