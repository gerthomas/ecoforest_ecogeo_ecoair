"""The few writable ecoAIR registers, with strict range checks (no Home Assistant imports).

Only registers that the documented ecoAIR Modbus table itself wires up as writable are listed:
the heat pump on/off-by-BUS register (5257), the BUS demand for shunt group SG1 (5183) and the
BUS heating setpoint for SG1 (170). Anything else is rejected before network I/O. To add a
control, add an entry to CONTROLS only after checking the manufacturer's documentation.
"""
from __future__ import annotations

import re

WRITE_REGISTER_OPERATION = 2012
_HEX4 = re.compile(r"^[0-9A-Fa-f]{4}$")

CONTROLS = {
    "air_ctl_bus_control": dict(
        platform="select", state_key="air_bus_control", bank="integer", address=5257,
        name="Heat pump on/off by BUS",
        options={0: "keyboard", 1: "off", 2: "on", 3: "emergency"}),
    "air_ctl_bus_demand_sg1": dict(
        platform="select", state_key="air_bus_demand_sg1", bank="integer", address=5183,
        name="BUS demand SG1",
        options={0: "nothing", 1: "heating", 2: "cooling"}),
    "air_ctl_bus_heating_setpoint_sg1": dict(
        platform="number", state_key="air_bus_heating_sg1_setpoint", bank="analog", address=170,
        name="BUS heating SG1 setpoint", min=0.0, max=60.0, step=0.1),
}

_BY_ADDRESS = {c["address"]: c for c in CONTROLS.values()}


def _hex(value: int) -> str:
    return f"{value & 0xFFFF:04X}"


def encode_control(control: dict, value) -> tuple[int, str]:
    """Return (register address, 4-digit hex value); raise ValueError if out of range."""
    if control["platform"] == "select":
        if type(value) is not int or value not in control["options"]:
            raise ValueError("Option not allowed for this control")
        return control["address"], _hex(value)
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError("Value must be a number") from err
    if not control["min"] <= number <= control["max"]:
        raise ValueError(f"Value must be between {control['min']} and {control['max']}")
    return control["address"], _hex(int(round(number * 10)))


def validate_write(data) -> None:
    """Accept only a single-register write to a listed control with an in-range value."""
    if not isinstance(data, dict):
        raise ValueError("Invalid write")
    extra = set(data) - {"idOperacion", "dir", "num"}
    if (len(extra) != 1 or data.get("idOperacion") != WRITE_REGISTER_OPERATION
            or type(data.get("dir")) is not int or data.get("num") != 1 or type(data["num"]) is not int):
        raise ValueError("Write not permitted")
    (key,) = extra
    if not isinstance(key, str) or not _HEX4.match(key) or data[key] != key:
        raise ValueError("Write payload must be one 4-digit hex value")
    control = _BY_ADDRESS.get(data["dir"])
    if control is None:
        raise ValueError("Register is not a permitted control")
    n = int(key, 16)
    n = n - 65536 if n >= 32768 else n
    if control["platform"] == "select":
        if n not in control["options"]:
            raise ValueError("Option not allowed for this control")
    elif not control["min"] <= n / 10 <= control["max"]:
        raise ValueError("Value out of range for this control")


def parse_write(response: str) -> None:
    lines = response.strip().splitlines()
    if not lines or lines[0].strip() != "error_geo_set_reg=0":
        raise ValueError("Write rejected by the heat pump")
