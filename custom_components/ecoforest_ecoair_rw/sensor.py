"""Support for Ecoforest sensors."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ALIAS
from homeassistant.helpers.typing import StateType

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoforestCoordinator
from .entity import EcoforestEntity, EcoforestSensorEntityDescription
from .overrides.device import EcoGeoDevice
from .overrides import api as api_module
from .entity import SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Ecoforest sensor platform."""
    coordinator: EcoforestCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    device_alias = config_entry.data[CONF_ALIAS] if CONF_ALIAS in config_entry.data else None
    mapping = coordinator.api.mapping
    entities = [
        EcoforestSensor(coordinator, key, definition, device_alias)
        for key, definition in mapping.items()
        if definition["entity_type"] in SENSOR_TYPES.keys()
    ]

    async_add_entities(entities)


class EcoforestSensor(SensorEntity, EcoforestEntity):
    """Representation of an Ecoforest sensor."""
    entity_description: EcoforestSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(self.data)

        return self.data.state.get(self.entity_description.key)

    @property
    def available(self):
        return super().available and self.data.state.get(self.entity_description.key) is not None

    @property
    def extra_state_attributes(self):
        definition = self.coordinator.api.mapping[self.entity_description.key]
        attributes = {'register_address': definition['address'],
                      'register_bank': definition.get('bank', definition['data_type']),
                      'read_only': True}
        for field in ('source', 'note'):
            if field in definition:
                attributes[field] = definition[field]
        if self.data.raw_values is not None:
            attributes['raw_value'] = self.data.raw_values.get(self.entity_description.key)
        return attributes
