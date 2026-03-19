"""Constants for the Zagonel Smart Shower integration."""

from datetime import timedelta

DOMAIN = "zagonel"
BASE_URL = "https://appsmartbanho.zagonel.com.br/api"
SCAN_INTERVAL = timedelta(minutes=10)

MANUFACTURER = "Zagonel"
MODEL = "Ducali Smart"

# Raw measurement field keys
FIELD_DURATION = "Du"
FIELD_FLOW_TOTAL = "Ft"
FIELD_TEMPERATURE = "Ta"
FIELD_VOLTAGE = "Va"
FIELD_POWER = "Pa"
FIELD_FLOW_RATE = "Fa"


def parse_measure(raw: dict, energy_price: float, water_price: float) -> dict:
    """Convert raw measurement data into human-readable values."""
    du = int(raw.get(FIELD_DURATION, 0))
    ft = int(raw.get(FIELD_FLOW_TOTAL, 0))
    ta = int(raw.get(FIELD_TEMPERATURE, 0))
    va = int(raw.get(FIELD_VOLTAGE, 0))
    pa = int(raw.get(FIELD_POWER, 0))
    fa = int(raw.get(FIELD_FLOW_RATE, 0))

    temp_c = ta / 1000
    flow_l_min = fa / 1000
    voltage_v = va / 1000
    water_l = ft / 1000

    max_power = 7500 if va > 150000 else 5500
    power_w = pa * max_power / 65535
    energy_kwh = (power_w / 1000) * (du / 3600)
    cost = energy_kwh * energy_price + water_l * water_price

    start_ts = int(raw.get("startTime", raw.get("timestamp", 0)))

    return {
        "start_time": start_ts,
        "duration": du,
        "temperature": round(temp_c, 1),
        "flow_rate": round(flow_l_min, 1),
        "voltage": round(voltage_v, 1),
        "power": round(power_w, 1),
        "energy": round(energy_kwh, 4),
        "water": round(water_l, 1),
        "cost": round(cost, 2),
        "hw": raw.get("Hw"),
        "fw": raw.get("Fw"),
    }
