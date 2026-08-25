"""Constants for the AlpicAir Heatpump integration.

Register map source: AlpicAir "Modbus Protocol (V1.6) for the Heat Pump
Water Heater" (RTU, function codes 0x01/0x03/0x0F/0x10).

IMPORTANT SCALING NOTE: the protocol document text states "accuracy: 1 C"
and "Transmission value = Actual value" for most temperature registers
(Word 118-137 etc.), implying no decimal scaling. In practice, on real
hardware these registers return the temperature as tenths of a degree
(x0.1 C) - confirmed empirically (e.g. a register value of 461 corresponds
to an actual tank temperature of 46.1 C, not 461 C). This is a known
mismatch between the printed protocol spec and the actual firmware
behaviour on AlpicAir units. All temperature registers are therefore
divided by 10 in the coordinator.
"""

DOMAIN = "alpicair_heatpump"

DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_NAME = "AlpicAir Heatpump"
DEFAULT_BAUDRATE = 9600

CONF_SLAVE = "slave"
CONF_CONNECTION_TYPE = "connection_type"
CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"

# --- Holding registers (Word 0-166), 0x03 read / 0x10 write ---
REG_MODE = 2
REG_OPTIONAL_EHEATER = 3
REG_DISINFECTION_TEMP = 4
REG_FLOOR_DEBUG_SEGMENTS = 5
REG_FLOOR_DEBUG_PERIOD1_TEMP = 6
REG_SEGMENT_DELTA_T = 7
REG_SEGMENT_TIME = 8
REG_WOT_COOL = 9
REG_WOT_HEAT = 10
REG_RT_COOL = 11
REG_RT_HEAT = 12
REG_T_WATER_TANK = 13
REG_T_EHEATER = 14
REG_T_OTHER_SWITCH_ON = 15
REG_T_HP_MAX = 16
REG_UPPER_AT_HEAT = 17
REG_LOWER_AT_HEAT = 18
REG_UPPER_RT_HEAT = 19
REG_LOWER_RT_HEAT = 20
REG_UPPER_WT_HEAT = 21
REG_LOWER_WT_HEAT = 22
REG_UPPER_AT_COOL = 23
REG_LOWER_AT_COOL = 24
REG_UPPER_RT_COOL = 25
REG_LOWER_RT_COOL = 26
REG_UPPER_WT_COOL = 27
REG_LOWER_WT_COOL = 28
REG_DELTA_T_COOL = 29
REG_DELTA_T_HEAT = 30
REG_DELTA_T_HOT_WATER = 31
REG_DELTA_T_ROOM_TEMP = 32
REG_COOL_RUN_TIME = 33
REG_HEAT_RUN_TIME = 34
REG_OTHER_THERMAL_LOGIC = 35
REG_TANK_HEATER = 36
REG_OPTIONAL_EHEATER_LOGIC = 37
REG_CURRENT_LIMIT = 38
REG_THERMOSTAT = 39
REG_FORCE_MODE = 40
REG_AIR_REMOVAL = 41
REG_ON_OFF = 42
REG_POWER_LIMIT = 43
REG_ERROR_RESET = 44

REG_UNIT_STATUS = 117
REG_T_OUTDOOR = 118
REG_T_DISCHARGE = 119
REG_T_DEFROST = 120
REG_T_SUCTION = 121
REG_T_ECONOMIZER_IN = 122
REG_T_ECONOMIZER_OUT = 123
REG_DIS_PRESSURE = 124
REG_T_WATER_OUT_PE = 125
REG_T_OPTIONAL_WATER_SEN = 126
REG_T_WATER_IN_PE = 127
REG_T_TANK_CTRL = 128
REG_T_REMOTE_ROOM = 129
REG_T_GAS_PIPE = 130
REG_T_LIQUID_PIPE = 131
REG_THERMOSTAT_STATE = 132
REG_T_FLOOR_DEBUG = 133
REG_DEBUG_TIME = 134
REG_DISINFECTION_STATE = 135
REG_ERROR_TIME_FLOOR_DEBUG = 136
REG_T_WEATHER_DEPEND = 137
REG_SETTING_FREQUENCY = 142
REG_RUNNING_FREQUENCY = 143

# --- State / control bits (Bit 0-199), 0x01 read / 0x0F write ---
BIT_WEEKLY_TIMER = 8
BIT_CLOCK_TIMER = 9
BIT_TEMP_TIMER = 10
BIT_GATE_CTRL = 11
BIT_SOLAR_HEATER = 16
BIT_CTRL_STATE = 17
BIT_FAST_HOT_WATER = 18
BIT_COOL_HOT_WATER_PRIORITY = 19
BIT_HEAT_HOT_WATER_PRIORITY = 20
BIT_QUIET_MODE = 21
BIT_WEATHER_DEPEND = 22
BIT_DISINFECTION = 23
BIT_FLOOR_DEBUG = 24
BIT_FLOOR_DEBUG_START_STOP = 25
BIT_EMERGENCY_MODE = 26
BIT_OTHER_THERMAL = 27
BIT_WATER_TANK = 29
BIT_SOLAR_SETTING = 31

ERROR_BITS = {
    64: "Ошибка связи: проводной пульт \u2194 внутренний блок",
    65: "Ошибка связи: проводной пульт \u2194 наружный блок",
    66: "Ошибка связи: проводной пульт \u2194 драйвер",
    67: "Защита от замерзания теплового насоса активна",
    88: "Ошибка датчика температуры окружающего воздуха",
    89: "Ошибка датчика температуры оттайки",
    90: "Ошибка датчика температуры нагнетания",
    91: "Ошибка датчика температуры всасывания",
    92: "Ошибка вентилятора наружного блока",
    93: "Ошибка датчика высокого давления",
    94: "Защита по высокому давлению",
    95: "Защита по низкому давлению",
    96: "Защита по высокой температуре нагнетания",
    97: "Ошибка настройки DIP переключателей мощности",
    98: "Ошибка связи между внутренним и наружным блоком",
    102: "Восстанавливаемая защита системы",
    103: "Невосстанавливаемая защита системы",
    108: "Защита по датчику потока",
    128: "Низкое напряжение / провал напряжения шины DC",
    129: "Повышенное напряжение шины DC",
    130: "Защита по току AC (входная сторона)",
    131: "Ошибка IPM",
    132: "Ошибка PFC",
    133: "Ошибка запуска",
    134: "Обрыв фазы",
    135: "Сброс силового модуля",
    136: "Перегрузка по току компрессора",
    137: "Превышение скорости",
    138: "Ошибка зарядной цепи или датчика тока",
    139: "Рассинхронизация",
    140: "Заклинивание компрессора",
    141: "Ошибка связи с драйвером",
    142: "Перегрев радиатора/IPM/PFC",
    143: "Неисправность радиатора/IPM/PFC",
    146: "Ошибка зарядной цепи",
    147: "Ошибка входного напряжения AC",
    148: "Ошибка датчика температуры платы драйвера",
    149: "Защита AC-контактора / ошибка перехода через ноль",
    150: "Защита от температурного дрейфа",
    151: "Защита по подключению датчика (фаза U/V)",
    152: "Ошибка датчика температуры воды на выходе конденсатора",
    153: "Ошибка датчика температуры воды на выходе электронагревателя",
    154: "Ошибка датчика температуры жидкого хладагента",
    155: "Ошибка датчика температуры воды на входе конденсатора",
    156: "Ошибка датчика температуры бака ГВС",
    158: "Ошибка датчика температуры паровой линии хладагента",
    160: "Ошибка датчика температуры удалённого пульта (комнатная)",
    184: "Ошибка перемычки (Jumper cap)",
    185: "Защита от подгорания электронагревателя 1",
    186: "Защита от подгорания электронагревателя 2",
    187: "Защита от подгорания нагревателя бака ГВС",
    188: "Защита по расходу воды",
    190: "Восстанавливаемая защита внутреннего блока",
    191: "Невосстанавливаемая защита внутреннего блока",
}

STATUS_BITS = {
    80: "Компрессор",
    81: "Вентилятор наружного блока",
    83: "4-ходовой клапан",
    84: "Нагреватель картера компрессора",
    85: "Нагреватель поддона",
    86: "Оттайка",
    87: "Возврат масла",
    169: "Другой источник тепла",
    170: "Реле потока",
    171: "Электронагреватель 1 (внутр.)",
    172: "Электронагреватель 2 (внутр.)",
    173: "Нагреватель бака ГВС",
    175: "Насос внутреннего блока",
    176: "Циркуляционный 2-ходовой клапан",
    177: "Пластинчатый нагреватель",
    178: "3-ходовой клапан",
}

MODE_MAP = {1: "heat", 2: "hot_water", 3: "cool_hot_water", 4: "heat_hot_water", 5: "cool"}
MODE_LABELS_RU = {
    "heat": "Обогрев",
    "hot_water": "Горячая вода",
    "cool_hot_water": "Охлаждение + ГВС",
    "heat_hot_water": "Обогрев + ГВС",
    "cool": "Охлаждение",
}

UNIT_STATUS_MAP = {0x01: "Охлаждение", 0x02: "Обогрев", 0x06: "Горячая вода", 0x08: "Выключено"}

ON_VALUE = 0xAA
OFF_VALUE = 0x55

MIN_TANK_TEMP = 40.0
MAX_TANK_TEMP = 80.0
TANK_TEMP_STEP = 1.0

# Word 10 - WOT_Heat: leaving water temperature setpoint in heating mode
MIN_WOT_HEAT_TEMP = 20.0
MAX_WOT_HEAT_TEMP = 60.0
WOT_HEAT_TEMP_STEP = 1.0
