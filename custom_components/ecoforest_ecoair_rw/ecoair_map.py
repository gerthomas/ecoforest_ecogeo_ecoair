"""ecoAIR sensor map built from the documented Ecoforest Modbus table (no HA imports).

Addresses are read through the register (2002) and coil (2001) reads that Easynet Geo
gateways already answer, so the existing read-only transport is reused unchanged.
Analog registers are signed tenths; integers are signed whole numbers; coils are 0/1.
"""
from __future__ import annotations

# bank|address|key|name|entity_type|extra   (extra: d = disabled by default, n:<note>)
_TABLE = """
analog|1|outlet_temp_indoor_unit|Outlet temperature indoor unit|temperature
analog|2|inlet_temp_indoor_unit|Inlet temperature indoor unit|temperature
analog|3|compressor_suction_intermediate|Compressor suction intermediate value|measurement|n:Documented as a temperature but with unit bar; meaning unverified.
analog|4|outlet_temp_outdoor_unit|Outlet temperature outdoor unit|temperature
analog|5|inlet_temp_outdoor_unit|Inlet temperature outdoor unit|temperature
analog|6|heating_circuit_pressure|Heating circuit pressure|pressure
analog|7|compressor_suction_pressure|Compressor suction pressure|pressure
analog|8|compressor_suction_temp|Compressor suction temperature|temperature
analog|9|compressor_discharge_pressure|Compressor discharge pressure|pressure
analog|10|compressor_discharge_temp|Compressor discharge temperature|temperature
analog|11|dhw_temperature|DHW temperature|temperature
analog|12|dhw_inlet_temperature|DHW inlet temperature|temperature
analog|13|supply_temp_sg2|Supply temperature SG2|temperature
analog|14|supply_temp_sg3_boiler|Supply temperature SG3 / boiler|temperature
analog|17|heating_buffer_tank_temp|Heating buffer tank temperature|temperature
analog|18|cooling_buffer_tank_temp|Cooling buffer tank temperature|temperature
analog|19|pool_temperature|Pool temperature|temperature
analog|20|outdoor_temperature|Outdoor temperature|temperature
analog|21|supply_temp_sg1|Supply temperature SG1|temperature
analog|23|heating_buffer_tank_setpoint|Heating buffer tank setpoint|temperature
analog|24|cooling_buffer_tank_setpoint|Cooling buffer tank setpoint|temperature
analog|25|condensation_temperature|Condensation temperature|temperature
analog|26|superheat|Superheat|temperature
analog|27|evaporation_temperature|Evaporation temperature|temperature
analog|28|expansion_valve_open|Expansion valve open|percent
analog|29|distribution_pump_regulation|Distribution pump regulation|percent
analog|30|fan_regulation|Fan regulation|percent
analog|31|shunt_sg2_regulation|Shunt group SG2 regulation|percent
analog|32|shunt_sg3_boiler_regulation|Shunt group SG3 / boiler regulation|percent
analog|33|shunt_sg1_regulation|Shunt group SG1 regulation|percent
analog|38|dhw_setpoint|DHW setpoint|temperature
analog|123|heating_sg1_setpoint|Heating SG1 setpoint|temperature
analog|124|heating_sg2_setpoint|Heating SG2 setpoint|temperature
analog|125|heating_sg3_setpoint|Heating SG3 setpoint|temperature
analog|128|cooling_sg1_setpoint|Cooling SG1 setpoint|temperature
analog|129|cooling_sg2_setpoint|Cooling SG2 setpoint|temperature
analog|130|cooling_sg3_setpoint|Cooling SG3 setpoint|temperature
analog|133|heating_power|Instantaneous heating power|power_kw
analog|134|cooling_power|Instantaneous cooling power|power_kw
analog|135|electric_power|Instantaneous electric power|power_kw
analog|136|cop|Instantaneous heating performance (COP)|measurement
analog|137|eer|Instantaneous cooling performance (EER)|measurement
analog|142|pool_setpoint|Pool setpoint|temperature
analog|151|bus_thermostat_setpoint_sg1|BUS thermostat setpoint SG1|temperature|d
analog|152|bus_thermostat_setpoint_sg2|BUS thermostat setpoint SG2|temperature|d
analog|153|bus_thermostat_setpoint_sg3|BUS thermostat setpoint SG3|temperature|d
analog|161|room_temp_terminal_1|Room temperature terminal 1|temperature|n:Only with a TH-Tune or THT terminal.
analog|162|room_temp_terminal_2|Room temperature terminal 2|temperature|n:Only with a TH-Tune or THT terminal.
analog|163|room_temp_terminal_3|Room temperature terminal 3|temperature|n:Only with a TH-Tune or THT terminal.
analog|168|bus_dhw_setpoint|BUS DHW setpoint|temperature|d
analog|169|bus_pool_setpoint|BUS pool setpoint|temperature|d
analog|170|bus_heating_sg1_setpoint|BUS heating SG1 setpoint|temperature|d
analog|171|bus_heating_sg2_setpoint|BUS heating SG2 setpoint|temperature|d
analog|172|bus_heating_sg3_setpoint|BUS heating SG3 setpoint|temperature|d
analog|175|bus_cooling_sg1_setpoint|BUS cooling SG1 setpoint|temperature|d
analog|176|bus_cooling_sg2_setpoint|BUS cooling SG2 setpoint|temperature|d
analog|177|bus_cooling_sg3_setpoint|BUS cooling SG3 setpoint|temperature|d
analog|182|indoor_circulator_regulation|Circulator pump indoor unit regulation|percent
analog|197|outlet_dt_outdoor_regulation|Outlet DT outdoor unit regulation|temperature
analog|198|outlet_dt_indoor_regulation|Outlet DT indoor unit regulation|temperature
analog|199|fan_dt_regulation|DT fan regulation|temperature
analog|200|frost_percent|Frost|percent
analog|223|compressor_reference|Current compressor reference|percent
analog|226|spf_month|Monthly SPF|measurement
analog|227|spf_year|Year SPF|measurement
integer|5002|compressor_speed|Compressor speed (rpm)|measurement
integer|5022|annual_heating_energy|Annual heating energy|raw|n:Unit (kWh or MWh) is set by coil 203.
integer|5023|annual_cooling_energy|Annual cooling energy|raw|n:Unit (kWh or MWh) is set by coil 204.
integer|5024|annual_electric_energy|Annual electric energy|raw|n:Unit (kWh or MWh) is set by coil 205.
integer|5159|room_humidity_zone_1|Room humidity zone 1|percent|n:Only with a TH-Tune or THT terminal.
integer|5160|room_humidity_zone_2|Room humidity zone 2|percent|n:Only with a TH-Tune or THT terminal.
integer|5161|room_humidity_zone_3|Room humidity zone 3|percent|n:Only with a TH-Tune or THT terminal.
integer|5181|bus_dhw_demand|BUS DHW demand|raw|d
integer|5182|bus_pool_demand|BUS pool demand|raw|d
integer|5183|bus_demand_sg1|BUS demand SG1|raw|d|n:0=nothing, 1=heating, 2=cooling.
integer|5184|bus_demand_sg2|BUS demand SG2|raw|d|n:0=nothing, 1=heating, 2=cooling.
integer|5185|bus_demand_sg3|BUS demand SG3|raw|d|n:0=nothing, 1=heating, 2=cooling.
integer|5188|heat_pump_program|Heat pump program|raw|n:0=nothing, 1=heating, 2=cooling.
integer|5257|bus_control|Heat pump on/off by BUS|raw|n:0=keyboard, 1=off, 2=on, 3=emergency.
coil|1|di_evu_signal|EVU signal (DI7)|raw
coil|2|di_summer_winter|Summer/winter selection (DI8)|raw
coil|3|di_dhw_activation|DHW activation (DI9)|raw
coil|4|di_pool_activation|Pool activation (DI10)|raw
coil|5|di_heating_demand_sg1|Heating demand SG1 (DI1)|raw
coil|6|di_cooling_demand_sg1|Cooling demand SG1 (DI2)|raw
coil|7|di_heating_demand_sg2|Heating demand SG2 (DI3)|raw
coil|8|di_cooling_demand_sg2|Cooling demand SG2 (DI4)|raw
coil|9|di_heating_demand_sg3|Heating demand SG3 (DI5)|raw
coil|10|di_cooling_demand_sg3|Cooling demand SG3 (DI6)|raw
coil|21|out_circulator_pump_hydraulic_kit|Circulator pump hydraulic kit|raw
coil|22|out_pool|Pool active|raw
coil|23|out_dhw|DHW active|raw
coil|24|out_dhw_recirculation|DHW recirculation active|raw
coil|25|out_production_valve|Production valve (0 heating, 1 cooling)|raw
coil|26|out_consumed_valve|Consumed valve (0 heating, 1 cooling)|raw
coil|27|out_sg1|SG1 active|raw
coil|28|out_sg2|SG2 active|raw
coil|29|out_sg3|SG3 active|raw
coil|30|out_aux_heater_buffer|Auxiliary equipment / buffer heater active|raw
coil|31|out_dhw_electric_heater|DHW electric heater active|raw
coil|32|out_alarm|Alarm signal (0 = no alarms)|raw
coil|33|out_fan|Fan active|raw
coil|34|out_outdoor_pump|Outdoor production pump active|raw
coil|35|out_cycle_inversion_valve|Cycle inversion valve|raw
coil|36|out_evi_valve|EVI valve|raw
coil|37|out_condensate_heater|Condensate tray heater active|raw
coil|180|bus_on_off|Heat pump on by BUS|raw
coil|201|program_summer|Program summer|raw
coil|202|program_winter|Program winter|raw
coil|203|units_heating_year_mwh|Annual heating energy unit (0 kWh, 1 MWh)|raw
coil|204|units_cooling_year_mwh|Annual cooling energy unit (0 kWh, 1 MWh)|raw
coil|205|units_electric_year_mwh|Annual electric energy unit (0 kWh, 1 MWh)|raw
"""

_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"]
_SOURCE = "Documented Ecoforest ecoAIR Modbus table (user-supplied)"


def _rows():
    for line in _TABLE.strip().splitlines():
        bank, address, key, name, etype, *extra = line.split("|")
        yield bank, int(address), key, name, etype, extra
    for i, (m, month) in enumerate(zip(_MONTHS, _MONTH_NAMES)):
        yield "analog", 211 + i, f"pf_{m}", f"Performance factor {month}", "measurement", ["d"]
        yield "integer", 5221 + i, f"cooling_energy_{m}", f"{month} cooling energy", "raw", ["d", "n:kWh or MWh, per the annual unit coils."]
        yield "integer", 5233 + i, f"heating_energy_{m}", f"{month} heating energy", "raw", ["d", "n:kWh or MWh, per the annual unit coils."]
        yield "integer", 5245 + i, f"electric_energy_{m}", f"{month} electric energy", "raw", ["d", "n:kWh or MWh, per the annual unit coils."]


def ecoair_register_mapping() -> dict:
    """Return key -> definition in the shape the shared read/decode helpers expect."""
    mapping = {}
    for bank, address, key, name, etype, extra in _rows():
        key = f"air_{key}"
        if key in mapping:
            raise ValueError(f"duplicate ecoAIR key {key}")
        definition = {
            "address": address, "name": name, "key": key, "rw": "R", "entity_type": etype,
            "scale": 0.1 if bank == "analog" else 1, "source": _SOURCE, "optional": True,
            "bank": "boolean" if bank == "coil" else bank,
            "data_type": 2 if bank == "coil" else 1,
        }
        for item in extra:
            if item == "d":
                definition["disabled_by_default"] = True
            elif item.startswith("n:"):
                definition["note"] = item[2:]
        mapping[key] = definition
    return mapping
