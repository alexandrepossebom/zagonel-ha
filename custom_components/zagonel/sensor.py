"""Sensor platform for Zagonel Smart Shower."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZagonelConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import ZagonelCoordinator


def _last(measures: list[dict]) -> dict | None:
    """Return the most recent measurement by start_time."""
    if not measures:
        return None
    return max(measures, key=lambda m: m.get("start_time", 0))


def _start_time(measures: list[dict]) -> datetime | None:
    last = _last(measures)
    if not last or not last["start_time"]:
        return None
    ts = last["start_time"]
    if ts > 1_000_000_000_000:
        ts = ts / 1000
    return datetime.fromtimestamp(ts, tz=UTC)


@dataclass(frozen=True, kw_only=True)
class ZagonelSensorDescription(SensorEntityDescription):
    """Describe a Zagonel sensor."""

    value_fn: Callable[[list[dict]], Any]
    attrs_fn: Callable[[list[dict]], dict[str, Any]] | None = None
    suggested_display_precision: int | None = None


LAST_SHOWER_SENSORS: tuple[ZagonelSensorDescription, ...] = (
    ZagonelSensorDescription(
        key="last_shower_time",
        translation_key="last_shower_time",
        name="Last Shower",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_start_time,
    ),
    ZagonelSensorDescription(
        key="last_shower_duration",
        translation_key="last_shower_duration",
        name="Last Shower Duration",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda m: _last(m)["duration"] if _last(m) else None,
        suggested_display_precision=0,
    ),
    ZagonelSensorDescription(
        key="last_shower_temperature",
        translation_key="last_shower_temperature",
        name="Last Shower Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda m: _last(m)["temperature"] if _last(m) else None,
        suggested_display_precision=1,
    ),
    ZagonelSensorDescription(
        key="last_shower_flow_rate",
        translation_key="last_shower_flow_rate",
        name="Last Shower Flow Rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="L/min",
        icon="mdi:water-pump",
        value_fn=lambda m: _last(m)["flow_rate"] if _last(m) else None,
        suggested_display_precision=1,
    ),
    ZagonelSensorDescription(
        key="last_shower_water",
        translation_key="last_shower_water",
        name="Last Shower Water",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda m: _last(m)["water"] if _last(m) else None,
        suggested_display_precision=1,
    ),
    ZagonelSensorDescription(
        key="last_shower_energy",
        translation_key="last_shower_energy",
        name="Last Shower Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda m: _last(m)["energy"] if _last(m) else None,
        suggested_display_precision=4,
    ),
    ZagonelSensorDescription(
        key="last_shower_power",
        translation_key="last_shower_power",
        name="Last Shower Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda m: _last(m)["power"] if _last(m) else None,
        suggested_display_precision=0,
    ),
    ZagonelSensorDescription(
        key="last_shower_voltage",
        translation_key="last_shower_voltage",
        name="Last Shower Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda m: _last(m)["voltage"] if _last(m) else None,
        suggested_display_precision=0,
    ),
    ZagonelSensorDescription(
        key="last_shower_cost",
        translation_key="last_shower_cost",
        name="Last Shower Cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="BRL",
        icon="mdi:currency-brl",
        value_fn=lambda m: _last(m)["cost"] if _last(m) else None,
        suggested_display_precision=2,
    ),
)


def _shower_list_attrs(measures: list[dict]) -> dict[str, Any]:
    """Build attributes with the list of all showers this month."""
    sorted_measures = sorted(measures, key=lambda m: m.get("start_time", 0))
    showers = []
    for m in sorted_measures:
        ts = m["start_time"]
        if ts > 1_000_000_000_000:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=UTC)
        mins, secs = divmod(m["duration"], 60)
        showers.append(
            {
                "date": dt.isoformat(),
                "duration": f"{mins}min {secs}s",
                "temperature": m["temperature"],
                "water_l": m["water"],
                "energy_kwh": m["energy"],
                "cost": m["cost"],
            }
        )
    return {"showers": showers}


MONTHLY_SENSORS: tuple[ZagonelSensorDescription, ...] = (
    ZagonelSensorDescription(
        key="monthly_shower_count",
        translation_key="monthly_shower_count",
        name="Showers This Month",
        icon="mdi:shower-head",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda m: len(m),
        attrs_fn=_shower_list_attrs,
        suggested_display_precision=0,
    ),
    ZagonelSensorDescription(
        key="monthly_water",
        translation_key="monthly_water",
        name="Monthly Water Usage",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda m: round(sum(x["water"] for x in m), 1),
        suggested_display_precision=1,
    ),
    ZagonelSensorDescription(
        key="monthly_energy",
        translation_key="monthly_energy",
        name="Monthly Energy Usage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda m: round(sum(x["energy"] for x in m), 4),
        suggested_display_precision=2,
    ),
    ZagonelSensorDescription(
        key="monthly_cost",
        translation_key="monthly_cost",
        name="Monthly Cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="BRL",
        icon="mdi:currency-brl",
        value_fn=lambda m: round(sum(x["cost"] for x in m), 2),
        suggested_display_precision=2,
    ),
)

ALL_SENSORS = LAST_SHOWER_SENSORS + MONTHLY_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZagonelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zagonel sensors from a config entry."""
    coordinator = entry.runtime_data

    entities: list[ZagonelSensorEntity] = []
    for shower_id in coordinator.data:
        shower_data = coordinator.data[shower_id]["shower"]
        for description in ALL_SENSORS:
            entities.append(
                ZagonelSensorEntity(coordinator, shower_id, shower_data, description)
            )

    async_add_entities(entities)


class ZagonelSensorEntity(CoordinatorEntity[ZagonelCoordinator], SensorEntity):
    """Representation of a Zagonel sensor."""

    entity_description: ZagonelSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZagonelCoordinator,
        shower_id: str,
        shower_data: dict,
        description: ZagonelSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._shower_id = shower_id
        self._attr_unique_id = f"{shower_id}_{description.key}"
        if description.suggested_display_precision is not None:
            self._attr_suggested_display_precision = (
                description.suggested_display_precision
            )

        # FW/HW come from measurements, not the shower object
        measures = coordinator.data.get(shower_id, {}).get("measures", [])
        last = measures[-1] if measures else {}

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, shower_id)},
            name=shower_data.get("showerName", "Zagonel Shower"),
            manufacturer=MANUFACTURER,
            model=MODEL,
            hw_version=last.get("hw"),
            sw_version=last.get("fw"),
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        data = self.coordinator.data.get(self._shower_id)
        if not data:
            return None
        measures = data.get("measures", [])
        return self.entity_description.value_fn(measures)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attrs_fn is None:
            return None
        data = self.coordinator.data.get(self._shower_id)
        if not data:
            return None
        return self.entity_description.attrs_fn(data.get("measures", []))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._shower_id in self.coordinator.data
