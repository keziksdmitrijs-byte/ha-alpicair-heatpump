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
    REG_UNIT_STATUS,
    REG_T_OUTDOOR,
    REG_T_WATER_OUT_PE,
    REG_T_WATER_IN_PE,
    REG_T_TANK_CTRL,
    REG_SETTING_FREQUENCY,
    REG_RUNNING_FREQUENCY,
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
            # Word 2-44: mode, setpoints, limits, on/off (control block)
            control_block = await self._client.read_holding_registers(
                address=2, count=43, **kw
            )
            # Word 117-137: live status, temperatures, thermostat state
            status_block = await self._client.read_holding_registers(
                address=117, count=21, **kw
            )
            # Word 142-143: setting/running frequency
            freq_block = await self._client.read_holding_registers(
                address=142, count=2, **kw
            )
            # Bit 64-199: errors and status flags (split to avoid the 100-116,
            # 144-167(partial) reserved gaps causing a whole-block exception)
            bits_8_31 = await self._client.read_coils(address=8, count=24, **kw)
            bits_64_111 = await self._client.read_coils(address=64, count=48, **kw)
            bits_128_199 = await self._client.read_coils(address=128, count=72, **kw)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Modbus read failed: {err}") from err

        for resp in (control_block, status_block, freq_block, bits_8_31, bits_64_111, bits_128_199):
            if resp.isError():
                raise UpdateFailed("Modbus device returned an error response")

        cb = control_block.registers  # index 0 -> Word 2
        mode = cb[0]                       # Word 2
        optional_eheater = cb[1]           # Word 3
        t_water_tank = cb[11]              # Word 13
        power_limit = cb[41] / 10.0        # Word 43 (x10 -> 0.1kW)
        on_off_raw = cb[40]                # Word 42

        sb = status_block.registers  # index 0 -> Word 117
        unit_status = sb[0]                # Word 117
        t_outdoor = self._to_signed16(sb[1])       # Word 118
        t_water_out_pe = self._to_signed16(sb[8])  # Word 125
        t_water_in_pe = self._to_signed16(sb[10])  # Word 127
        t_tank_ctrl = self._to_signed16(sb[11])    # Word 128
        thermostat_state = sb[15]          # Word 132

        setting_frequency = freq_block.registers[0]   # Word 142
        running_frequency = freq_block.registers[1]   # Word 143

        # Merge coil blocks into one address->bit lookup for convenience
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

    async def async_write_tank_setpoint(self, celsius: float) -> None:
        await self.async_write_register(REG_T_WATER_TANK, int(round(celsius)))

    async def async_write_coil_bit(self, bit_address: int, state: bool) -> None:
        kw = {self._device_kwarg: self._slave}
        await self._client.write_coil(bit_address, state, **kw)
        await self.async_request_refresh()
