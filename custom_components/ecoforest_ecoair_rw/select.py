"""Select controls (opt-in)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ALIAS
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
        EcoforestSelect(coordinator, key, control, alias)
        for key, control in CONTROLS.items() if control["platform"] == "select"
    )


class EcoforestSelect(EcoforestControlEntity, SelectEntity):
    """Choose one of a few documented values."""

    def __init__(self, coordinator, key, control, device_alias) -> None:
        super().__init__(coordinator, key, control, device_alias)
        self._attr_options = list(control["options"].values())

    @property
    def current_option(self) -> str | None:
        value = self.raw_state
        return None if value is None else self._control["options"].get(int(value))

    async def async_select_option(self, option: str) -> None:
        by_label = {label: n for n, label in self._control["options"].items()}
        if option not in by_label:
            return
        await self._write(by_label[option])
