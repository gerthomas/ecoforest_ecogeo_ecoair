"""Base Entity for Ecoforest."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPower,
    UnitOfPressure,
    UnitOfEnergy,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription, generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify

from .const import DOMAIN, MANUFACTURER
from .coordinator import EcoforestCoordinator
from .overrides.device import EcoGeoDevice


SENSOR_TYPES = {
    "temperature": {
        "class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "pressure": {"class": SensorDeviceClass.PRESSURE, "unit": UnitOfPressure.BAR},
    "power": {"class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT},
    "power_kw": {"class": SensorDeviceClass.POWER, "unit": UnitOfPower.KILO_WATT},
    "energy": {"class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.WATT_HOUR},
    "energy_kwh": {
        "class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
    },
    "energy_mwh": {
        "class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.MEGA_WATT_HOUR,
    },
    "raw": {},
    "percent": {"unit": "%"},
    "measurement": {"state_class": SensorStateClass.MEASUREMENT},
    "enum": {"class": SensorDeviceClass.ENUM},
    "duration_min": {
        "class": SensorDeviceClass.DURATION,
        "unit": UnitOfTime.MINUTES,
    },
}


@dataclass(frozen=True, kw_only=True)
class EcoforestSensorEntityDescription(SensorEntityDescription):
    """Describes Ecoforest sensor entity."""

    value_fn: Callable[[EcoGeoDevice], StateType] | None = None


class EcoforestEntity(CoordinatorEntity[EcoforestCoordinator]):
    """Common Ecoforest entity using CoordinatorEntity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoforestCoordinator,
        key: str,
        definition: dict[str, str],
        device_alias: str,
    ) -> None:
        """Initialize device information."""

        if definition["entity_type"] in SENSOR_TYPES.keys():
            self.entity_description = EcoforestSensorEntityDescription(
                key=key,
                translation_key=key,
                options=list(dict.fromkeys(definition["enum"].values())) if "enum" in definition else None,
                native_unit_of_measurement=(
                    SENSOR_TYPES[definition["entity_type"]]["unit"]
                    if "unit" in SENSOR_TYPES[definition["entity_type"]].keys()
                    else None
                ),
                device_class=(
                    SENSOR_TYPES[definition["entity_type"]]["class"]
                    if "class" in SENSOR_TYPES[definition["entity_type"]].keys()
                    else None
                ),
                entity_registry_enabled_default=not definition.get("disabled_by_default", False),
                state_class=(
                    SENSOR_TYPES[definition["entity_type"]]["state_class"]
                    if "state_class" in SENSOR_TYPES[definition["entity_type"]].keys()
                    else None
                ),
            )
        else:
            self.entity_description = EcoforestSensorEntityDescription(
                key=key, translation_key=key
            )

        device_id = (
            coordinator.data.model_name if device_alias is None else device_alias
        )
        device_name = MANUFACTURER if device_alias is None else device_alias

        id = f"{device_id}_{key}"
        self._attr_unique_id = id
        self.entity_id = f"sensor.{slugify(id)}"

        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            model=coordinator.data.model_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def data(self) -> EcoGeoDevice:
        """Return ecoforest data."""
        assert self.coordinator.data
        return self.coordinator.data


class EcoforestControlEntity(CoordinatorEntity[EcoforestCoordinator]):
    """Base for the opt-in control entities (select and number)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EcoforestCoordinator, key: str, control: dict,
                 device_alias: str | None) -> None:
        super().__init__(coordinator)
        self._key = key
        self._control = control
        device_id = coordinator.data.model_name if device_alias is None else device_alias
        device_name = MANUFACTURER if device_alias is None else device_alias
        self._attr_translation_key = key
        self._attr_unique_id = f"{device_id}_{key}"
        self.entity_id = f"{control['platform']}.{slugify(f'{device_id}_{key}')}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            model=coordinator.data.model_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def raw_state(self):
        assert self.coordinator.data
        return self.coordinator.data.state.get(self._control["state_key"])

    @property
    def available(self) -> bool:
        return super().available and self.raw_state is not None

    async def _write(self, value) -> None:
        from homeassistant.exceptions import HomeAssistantError
        try:
            await self.coordinator.api.write_control(self._key, value)
        except Exception as err:  # surface any failure in the UI instead of silently ignoring it
            raise HomeAssistantError(f"Could not set {self._control['name']}: {err}") from err
        await self.coordinator.async_request_refresh()
