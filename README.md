# AlpicAir Heatpump — Home Assistant Integration

Custom HACS integration for controlling **AlpicAir** heat pump water heaters
over Modbus (native protocol: RTU on RS-485, 9600 8N1). Register map is
taken directly from the official "Modbus Protocol (V1.6) for the Heat Pump
Water Heater" document, which explicitly references AlpicAir's long-distance
monitoring system.

## Installation via HACS

1. HACS → Integrations → three-dot menu → **Custom repositories**.
2. Add `https://github.com/keziksdmitrijs-byte/ha-alpicair-heatpump`, category **Integration**.
3. Install **AlpicAir Heatpump**, restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → search "AlpicAir Heatpump".
5. Choose connection type:
   - **TCP** — if your RS-485 bus is bridged to Modbus TCP via a gateway (enter IP + port).
   - **Serial** — if Home Assistant has direct access to the RS-485 adapter (enter serial device path, e.g. `/dev/ttyUSB0`, and baud rate, default 9600).
6. Enter the Modbus slave/device address configured on the unit's wired controller (valid range 1-255, cannot be 0 or 126).

## Entities created

| Platform | Entity | Register | Notes |
|---|---|---|---|
| select | Режим работы | Word 2 | Heat / Hot water / Cool+Hot water / Heat+Hot water / Cool |
| button | Включить / Выключить | Word 42 | 0xAA=On, 0x55=Off |
| button | Сбросить ошибку | Word 44 | |
| number | Целевая температура бака ГВС | Word 13 | 40-80 °C |
| number | Лимит мощности | Word 43 | 0-10 kW (config category) |
| switch | Тихий режим | Bit 21 | |
| switch | Погодозависимый режим | Bit 22 | |
| switch | Дезинфекция бака | Bit 23 | |
| switch | Быстрый нагрев ГВС | Bit 18 | |
| sensor | Текущий статус блока | Word 117 | Cool/Heat/HotWater/Off |
| sensor | Температура наружного воздуха | Word 118 | °C, signed |
| sensor | Температура воды на входе/выходе теплообменника | Word 125/127 | °C, signed |
| sensor | Температура бака ГВС (датчик) | Word 128 | °C, signed |
| sensor | Текущая/заданная частота компрессора | Word 143/142 | Hz |
| sensor | Количество активных ошибок / Текущие ошибки | Bit 64-199 | decoded to Russian text, full list in attributes |
| sensor | Активные состояния оборудования | Bit 80-178 | compressor, fan, defrost, pumps, valves, etc. |

## Important operational notes (from the manufacturer's protocol)

- **Mode changes only take effect while the unit is off.** Attempting to
  change "Режим работы" while the heat pump is running is rejected by the
  device itself.
- For heating-only units, Cool and Cool+Hot Water mode settings have no effect.
- If no water tank is installed, Hot Water / Cool+Hot Water / Heat+Hot Water /
  Disinfection / Fast Hot Water settings have no effect.
- "Целевая температура бака ГВС" only takes effect when Disinfection is off.
- Any configuration change is applied immediately but only persisted to the
  unit's memory after 30 minutes, per the protocol document.

## Register map summary

Full register map (Word 0-166 holding registers, Bit 0-199 coils/status) is
implemented in `const.py`, filtered to the subset relevant for monitoring and
control from Home Assistant. See the source protocol PDF for the complete
specification, including floor heating debug sections, solar heater
integration, and detailed outdoor/indoor unit diagnostics not yet exposed as
entities.

## Disclaimer

Not affiliated with or endorsed by AlpicAir. Verify register addresses
against your unit's specific documentation before use — the protocol
explicitly warns that "Modes are allowed to be changed only when the unit is
off, or this operation is ineffective."
