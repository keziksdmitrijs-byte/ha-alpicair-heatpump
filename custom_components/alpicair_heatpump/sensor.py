"""Sensor platform for AlpicAir Heatpump."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, UNIT_STATUS_MAP

TEMPERATURE_SENSORS = [
    ("t_outdoor", "Температура наружного воздуха", "mdi:thermometer"),
    ("t_water_out_pe", "Температура воды на выходе теплообменника", "mdi:thermometer-water"),
    ("t_water_in_pe", "Температура воды на входе теплообменника", "mdi:thermometer-water"),
    ("t_tank_ctrl", "Температура бака ГВС (датчик)", "mdi:thermometer-water"),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        AlpicAirHeatpumpUnitStatusSensor(coordinator, entry),
        AlpicAirHeatpumpRunningFrequencySensor(coordinator, entry),
        AlpicAirHeatpumpSettingFrequencySensor(coordinator, entry),
        AlpicAirHeatpumpErrorCountSensor(coordinator, entry),
        AlpicAirHeatpumpErrorTextSensor(coordinator, entry),
        AlpicAirHeatpumpStatusTextSensor(coordinator, entry),
    ]
    entities += [AlpicAirHeatpumpTemperatureSensor(coordinator, entry, k, n, i) for k, n, i in TEMPERATURE_SENSORS]
    async_add_entities(entities)


class _Base(CoordinatorEntity, SensorEntity):
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


class AlpicAirHeatpumpTemperatureSensor(_Base):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, data_key: str, name: str, icon: str) -> None:
        super().__init__(coordinator, entry)
        self._data_key = data_key
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)


class AlpicAirHeatpumpUnitStatusSensor(_Base):
    _attr_icon = "mdi:heat-pump"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_unit_status"
        self._attr_name = "Текущий статус блока"

    @property
    def native_value(self):
        raw = self.coordinator.data.get("unit_status")
        return UNIT_STATUS_MAP.get(raw, f"Неизвестно (#{raw})")


class AlpicAirHeatpumpRunningFrequencySensor(_Base):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Hz"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_running_frequency"
        self._attr_name = "Текущая частота компрессора"

    @property
    def native_value(self):
        return self.coordinator.data.get("running_frequency")


class AlpicAirHeatpumpSettingFrequencySensor(_Base):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Hz"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_setting_frequency"
        self._attr_name = "Заданная частота компрессора"

    @property
    def native_value(self):
        return self.coordinator.data.get("setting_frequency")


class AlpicAirHeatpumpErrorCountSensor(_Base):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_error_count"
        self._attr_name = "Количество активных ошибок"

    @property
    def native_value(self):
        return self.coordinator.data.get("error_count")


class AlpicAirHeatpumpErrorTextSensor(_Base):
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_error_text"
        self._attr_name = "Текущие ошибки теплового насоса"

    @property
    def native_value(self):
        errors = self.coordinator.data.get("active_errors") or []
        return errors[0] if errors else "Нет активных ошибок"

    @property
    def extra_state_attributes(self):
        return {"all_errors": self.coordinator.data.get("active_errors") or []}


class AlpicAirHeatpumpStatusTextSensor(_Base):
    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_status_text"
        self._attr_name = "Активные состояния оборудования"

    @property
    def native_value(self):
        statuses = self.coordinator.data.get("active_status") or []
        return ", ".join(statuses) if statuses else "Нет активных состояний"

    @property
    def extra_state_attributes(self):
        return {"all_status": self.coordinator.data.get("active_status") or []}
