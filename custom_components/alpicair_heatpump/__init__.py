"""The AlpicAir Heatpump integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SLAVE, CONF_CONNECTION_TYPE, CONF_SERIAL_PORT, CONF_BAUDRATE
from .coordinator import AlpicAirHeatpumpCoordinator

PLATFORMS = ["sensor", "number", "switch", "button", "select"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    coordinator = AlpicAirHeatpumpCoordinator(
        hass,
        connection_type=data.get(CONF_CONNECTION_TYPE, "tcp"),
        host=data.get(CONF_HOST),
        port=data.get(CONF_PORT),
        serial_port=data.get(CONF_SERIAL_PORT),
        baudrate=data.get(CONF_BAUDRATE, 9600),
        slave=data[CONF_SLAVE],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
