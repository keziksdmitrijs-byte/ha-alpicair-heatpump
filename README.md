# AlpicAir Heatpump — Home Assistant Integration

## v0.3.0 — fix: temperature readings were 10x too high

**Root cause:** the printed protocol document ("Modbus Protocol V1.6 for the
Heat Pump Water Heater") states accuracy "1 C" and "Transmission value =
Actual value" for the live temperature sensors (Word 118, 125, 127, 128,
etc.), implying the register holds the temperature directly in whole
degrees. On real AlpicAir hardware this is incorrect: these registers
actually return the temperature in **tenths of a degree** (x0.1 C). A raw
register value of 461 is an actual temperature of 46.1 C, not 461 C.

This was confirmed against a live dashboard where "Температура бака ГВС"
showed 461.0 °C, "Температура воды на входе" showed 422.0 °C, etc. — all
exactly 10x the physically plausible values (46.1 °C, 42.2 °C, ...).

**Fix:** `t_outdoor`, `t_water_out_pe`, `t_water_in_pe`, and `t_tank_ctrl` are
now divided by 10 in the coordinator. `t_water_tank_setpoint` (Word 13, the
target setpoint, range 40-80) is left unscaled, since that register's
documented range and behavior matches whole-degree values.

## v0.2.0 — single power switch/button instead of separate On/Off

- `switch.питание` — shows current power state and toggles it.
- `button.включитьвыключить` — single tap-to-toggle button, alternative to the switch.

## Installation via HACS

1. HACS → Integrations → three-dot menu → **Custom repositories**.
2. Add `https://github.com/keziksdmitrijs-byte/ha-alpicair-heatpump`, category **Integration**.
3. Install **AlpicAir Heatpump**, restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → search "AlpicAir Heatpump".
5. Choose connection type (TCP via gateway, or direct Serial/RS-485) and enter
   the Modbus slave/device address configured on the unit's wired controller.

If you already have this integration installed and see temperature readings
that look exactly 10x too high, update to this version via HACS and restart
Home Assistant — no reconfiguration is needed, the fix is purely in how the
raw register values are interpreted.

## Entities created

| Platform | Entity | Register | Notes |
|---|---|---|---|
| select | Режим работы | Word 2 | Heat / Hot water / Cool+Hot water / Heat+Hot water / Cool |
| switch | Питание | Word 42 | On/Off with state indicator |
| button | Включить/Выключить | Word 42 | Single tap-to-toggle button |
| button | Сбросить ошибку | Word 44 | |
| number | Целевая температура бака ГВС | Word 13 | 40-80 °C, NOT scaled |
| number | Лимит мощности | Word 43 | 0-10 kW, x10 scale (config category) |
| switch | Тихий режим / Погодозависимый режим / Дезинфекция бака / Быстрый нагрев ГВС | Bit 21/22/23/18 | |
| sensor | Текущий статус блока | Word 117 | Cool/Heat/HotWater/Off |
| sensor | Температура наружного воздуха / воды на входе-выходе теплообменника / бака ГВС | Word 118/125/127/128 | °C, **x0.1 scale**, signed |
| sensor | Текущая/заданная частота компрессора | Word 143/142 | Hz |
| sensor | Количество активных ошибок / Текущие ошибки / Активные состояния оборудования | Bit 64-199 | decoded to Russian, full list in attributes |

## Disclaimer

Not affiliated with or endorsed by AlpicAir. Verify register addresses and
scaling against your own unit's actual behavior — as this release
demonstrates, the printed protocol specification does not always match real
firmware behavior.
