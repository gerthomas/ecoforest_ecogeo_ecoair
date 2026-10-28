# Ecoforest EcoAir (read/write) for Home Assistant

Ecoforest ecoAIR heat pump integration PoC (proof of concept, thus may lack features or stability).
Fork of [bytestorm/ecoforest_ecogeo](https://github.com/bytestorm/ecoforest_ecogeo), reworked for ecoAIR units using the
documented ecoAIR Modbus table. The read side is shared with the read-only fork `ecoforest_ecoair_ro`
(based on [ostracon/ecoforest_ecogeo](https://github.com/ostracon/ecoforest_ecogeo)); credit to both authors.

**Status:** the sensors were tested on an ecoAIR through an Easynet Geo 2.13 gateway (read-only fork). The write path and the
control entities in this fork have only been tested against simulated responses; try them with care.

## Install

1. In HACS, add this repository as a custom repository (category: Integration), install, restart Home Assistant.
2. Settings -> Devices & Services -> Add integration -> "Ecoforest EcoAir (read/write)".
3. Fields:
   - **Ecoforest Easynet URL**: the web address of the gateway, e.g. `http://192.168.1.200/`
   - **Username**: the heat pump serial number (same as the web interface)
   - **Password**: the first 8 characters of the original wireless network password (same as the web interface)
   - **Alias** (optional): used instead of the model name for entity prefixes
   - **Allow control (writes)**: off by default. With it off the integration never writes to the heat pump.

Do not run this at the same time as another Ecoforest integration polling the same gateway, and remove other forks
(`ecoforest_ecoair_ro`, the original ecogeo) first so entities do not clash. To change the control option later, remove and re-add the integration.

## Sensors

160 sensors from the documented table (temperatures on both units, pressures, fan/pump/valve regulation, setpoints,
instantaneous power in kW, COP/EER, compressor speed and reference, coils as 0/1, annual and monthly energy counters).
Monthly counters, performance factors and BUS setpoints are disabled by default. Entity ids contain `air_`
(for example `sensor.<model>_air_outdoor_temperature`). Energy counters are raw numbers; kWh or MWh follows coils 203-205.

## Controls (only with "Allow control" ticked)

Only registers the documented table itself shows as writable are exposed:

| Entity | Register | Values |
|---|---|---|
| Heat pump on/off by BUS (select) | 5257 | keyboard, off, on, emergency |
| BUS demand SG1 (select) | 5183 | nothing, heating, cooling |
| BUS heating SG1 setpoint (number) | 170 | 0 to 60 degrees C |

These change how the heat pump runs. "keyboard" hands control back to the unit; "emergency" is the unit's emergency mode.
Every write is checked before it is sent (exact register, exact value range, single register), then read back and logged if it
differs. Nothing else can be written: other BUS registers are deliberately not exposed until they are verified against the manufacturer's
documentation. To add one, extend `CONTROLS` in `ecoair_controls.py` and the tests.

`Registers.csv` in this repository is the generic ecoGEO table. The same addresses mean different things on ecoAIR
(for example address 175 is a compressor limit there but a BUS setpoint here), so never use it to decide what is safe to write.

---

Custom visualization:

![flow](https://github.com/YOUR-GITHUB-USERNAME/ecoforest_ecogeo_ecoair/blob/master/flow.png?raw=true)

<details>
  <summary>Details...</summary>
  
  This card is built using [power-flow-card-plus](https://github.com/flixlix/power-flow-card-plus). You can install it with HACS.<br />
  Just replace entity prefixes (ebfhbb in my case) with the model name or the alias of your heat pump.


```yaml
type: custom:power-flow-card-plus
entities:
  grid:
    entity: sensor.<model>_air_electric_power
    display_state: one_way_no_zero
    name: Consumption
    color:
      consumption:
        - 78
        - 122
        - 39
  home:
    entity: sensor.<model>_air_heating_power
    icon: mdi:hvac
    subtract_individual: false
    override_state: true
    secondary_info:
      entity: sensor.<model>_air_outdoor_temperature
      unit_of_measurement: °C
      decimals: 1
  individual:
    - entity: sensor.ebfhbb_power_cooling
      display_zero_state: false
      name: Cooling
      secondary_info:
        entity: sensor.ebfhbb_t_cooling
        unit_of_measurement: °C
        display_zero: false
        decimals: 1
      icon: mdi:snowflake
      display_zero: true
      color:
        - 0
        - 213
        - 255
    - entity: sensor.ebfhbb_power_heating
      display_zero: true
      name: Heating
      icon: mdi:heating-coil
      secondary_info:
        entity: sensor.ebfhbb_t_heating
        unit_of_measurement: °C
      color:
        - 203
        - 37
        - 37
      decimals: 1
      display_zero_state: false
    - name: DHW
      icon: mdi:water-boiler
      color:
        - 212
        - 154
        - 28
      decimals: 1
      display_zero: true
      secondary_info:
        entity: sensor.ebfhbb_t_dhw
        unit_of_measurement: °C
        decimals: 1
      display_zero_state: false
      entity: '0'
clickable_entities: true
display_zero_lines:
  mode: show
  transparency: 50
  grey_color:
    - 189
    - 189
    - 189
use_new_flow_rate_model: true
w_decimals: 0
kw_decimals: 1
min_flow_rate: 5
max_flow_rate: 5
max_expected_power: 2000
min_expected_power: 0.01
watt_threshold: 1000
transparency_zero_lines: 0
disable_dots: true
```
</details>
