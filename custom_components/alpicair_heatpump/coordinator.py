"""DataUpdateCoordinator for the AlpicAir Heatpump integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import pymodbus
from packaging import version

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    REG_MODE,
    REG_ON_OFF,
    REG_T_WATER_TANK,
    REG_POWER_LIMIT,
    ERROR_BITS,
    STATUS_BITS,
    ON_VALUE,
    OFF_VALUE,
    BIT_QUIET_MODE,
    BIT_WEATHER_DEPEND,
    BIT_DISINFECTION,
    BIT_FAST_HOT_WATER,
)

_LOGGER = logging.getLogger(__name__)


def _device_kwarg_name() -> str:
    """Return 'device_id' or 'slave' depending on the installed pymodbus version."""
    try:
        if version.parse(pymodbus.__version__) >= version.parse("3.10.0"):
            return "device_id"
    except Exception:  # noqa: BLE001
        pass
    return "slave"


class AlpicAirHeatpumpCoordinator(DataUpdateCoordinator):
    """Polls the AlpicAir heat pump water heater over Modbus (RTU or TCP gateway)."""

    def __init__(
        self,
        hass: HomeAssistant,
        connection_type: str,
        host: str | None,
        port: int | None,
        serial_port: str | None,
        baudrate: int,
        slave: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="alpicair_heatpump",
            update_interval=timedelta(seconds=20),
        )
        self._connection_type = connection_type
        self._host = host
        self._port = port
        self._slave = slave
        self._device_kwarg = _device_kwarg_name()

        if connection_type == "serial":
            self._client = AsyncModbusSerialClient(
                port=serial_port,
                baudrate=baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
            )
        else:
            self._client = AsyncModbusTcpClient(host=host, port=port)

    async def _async_update_data(self) -> dict:
        if not self._client.connected:
            await self._client.connect()
        if not self._client.connected:
            target = self._host if self._connection_type == "tcp" else "serial port"
            raise UpdateFailed(f"Cannot connect to {target}")

        kw = {self._device_kwarg: self._slave}

        try:
            control_block = await self._client.read_holding_registers(address=2, count=43, **kw)
            status_block = await self._client.read_holding_registers(address=117, count=21, **kw)
            freq_block = await self._client.read_holding_registers(address=142, count=2, **kw)
            bits_8_31 = await self._client.read_coils(address=8, count=24, **kw)
            bits_64_111 = await self._client.read_coils(address=64, count=48, **kw)
            bits_128_199 = await self._client.read_coils(address=128, count=72, **kw)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Modbus read failed: {err}") from err

        for resp in (control_block, status_block, freq_block, bits_8_31, bits_64_111, bits_128_199):
            if resp.isError():
                raise UpdateFailed("Modbus device returned an error response")

        cb = control_block.registers  # index 0 -> Word 2
        mode = cb[0]
        optional_eheater = cb[1]
        t_water_tank = cb[11]              # Word 13 setpoint - protocol confirms integer C here (40-80 range, no x10)
        power_limit = cb[41] / 10.0        # Word 43, explicit x10 -> 0.1kW per protocol
        on_off_raw = cb[40]

        sb = status_block.registers  # index 0 -> Word 117
        unit_status = sb[0]
        # Live temperature sensors (Word 118-137): protocol text says "accuracy 1 C"
        # but real hardware returns tenths of a degree (e.g. raw 461 = 46.1 C).
        # Confirmed empirically against known-good reference temperatures, so all
        # of these are divided by 10 despite the printed spec.
        t_outdoor = self._to_signed16(sb[1]) / 10.0          # Word 118
        t_water_out_pe = self._to_signed16(sb[8]) / 10.0     # Word 125
        t_water_in_pe = self._to_signed16(sb[10]) / 10.0     # Word 127
        t_tank_ctrl = self._to_signed16(sb[11]) / 10.0       # Word 128
        thermostat_state = sb[15]                            # Word 132, mode code - not scaled

        setting_frequency = freq_block.registers[0]
        running_frequency = freq_block.registers[1]

        bits: dict[int, bool] = {}
        for i, val in enumerate(bits_8_31.bits[:24]):
            bits[8 + i] = bool(val)
        for i, val in enumerate(bits_64_111.bits[:48]):
            bits[64 + i] = bool(val)
        for i, val in enumerate(bits_128_199.bits[:72]):
            bits[128 + i] = bool(val)

        active_errors = [ERROR_BITS[addr] for addr, is_set in bits.items() if is_set and addr in ERROR_BITS]
        active_status = [STATUS_BITS[addr] for addr, is_set in bits.items() if is_set and addr in STATUS_BITS]

        return {
            "quiet_mode": bits.get(BIT_QUIET_MODE, False),
            "weather_depend": bits.get(BIT_WEATHER_DEPEND, False),
            "disinfection": bits.get(BIT_DISINFECTION, False),
            "fast_hot_water": bits.get(BIT_FAST_HOT_WATER, False),
            "mode": mode,
            "optional_eheater": optional_eheater,
            "t_water_tank_setpoint": t_water_tank,
            "power_limit_kw": power_limit,
            "is_on": on_off_raw == ON_VALUE,
            "unit_status": unit_status,
            "t_outdoor": t_outdoor,
            "t_water_out_pe": t_water_out_pe,
            "t_water_in_pe": t_water_in_pe,
            "t_tank_ctrl": t_tank_ctrl,
            "thermostat_state": thermostat_state,
            "setting_frequency": setting_frequency,
            "running_frequency": running_frequency,
            "active_errors": active_errors,
            "active_status": active_status,
            "error_count": len(active_errors),
        }

    @staticmethod
    def _to_signed16(value: int) -> int:
        return value - 65536 if value > 32767 else value

    async def async_write_register(self, address: int, value: int) -> None:
        kw = {self._device_kwarg: self._slave}
        await self._client.write_register(address, value, **kw)
        await self.async_request_refresh()

    async def async_write_mode(self, value: int) -> None:
        await self.async_write_register(REG_MODE, value)

    async def async_write_on_off(self, on: bool) -> None:
        await self.async_write_register(REG_ON_OFF, ON_VALUE if on else OFF_VALUE)

    async def async_toggle_power(self) -> None:
        current_is_on = bool(self.data.get("is_on")) if self.data else False
        await self.async_write_on_off(not current_is_on)

    async def async_write_tank_setpoint(self, celsius: float) -> None:
        await self.async_write_register(REG_T_WATER_TANK, int(round(celsius)))

    async def async_write_coil_bit(self, bit_address: int, state: bool) -> None:
        kw = {self._device_kwarg: self._slave}
        await self._client.write_coil(bit_address, state, **kw)
        await self.async_request_refresh()
