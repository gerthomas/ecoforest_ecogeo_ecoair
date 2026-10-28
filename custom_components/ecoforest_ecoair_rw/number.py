"""Number controls (opt-in)."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ALIAS, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .ecoair_controls import CONTROLS
from .entity import EcoforestControlEntity


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    alias = config_entry.data.get(CONF_ALIAS)
    async_add_entities(
        EcoforestNumber(coordinator, key, control, alias)
        for key, control in CONTROLS.items() if control["platform"] == "number"
    )


class EcoforestNumber(EcoforestControlEntity, NumberEntity):
    """A setpoint with the documented range."""

    _attr_mode = NumberMode.BOX
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, key, control, device_alias) -> None:
        super().__init__(coordinator, key, control, device_alias)
        self._attr_native_min_value = control["min"]
        self._attr_native_max_value = control["max"]
        self._attr_native_step = control["step"]

    @property
    def native_value(self) -> float | None:
        return self.raw_state

    async def async_set_native_value(self, value: float) -> None:
        await self._write(value)
