"""Sensor platform for the Smart-me integration.

Each smart-me device becomes one HA "device" with up to two entities:
- a cumulative counter reading (device_class energy/water/gas, state_class
  total_increasing) - this is what the Energy dashboard needs.
- an instantaneous power/flow reading, when the API reports one.

The device_class is derived from the device's `deviceEnergyType` reported by
the smart-me API, so electricity, water (warm/cold), gas and heat meters are
all picked up automatically - no need to hardcode which device is "which".
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENERGY_TYPE_ELECTRICITY,
    ENERGY_TYPE_GAS,
    ENERGY_TYPE_HEAT,
    ENERGY_TYPE_WATER,
    SUB_TYPE_COLD_WATER,
    SUB_TYPE_HOT_WATER,
)
from .coordinator import SmartMeCoordinator

# smart-me reports Heat meters in kWh as well, HA has no separate "heat"
# device_class, so it is mapped onto "energy" like electricity.
ENERGY_TYPE_DEVICE_CLASS = {
    ENERGY_TYPE_ELECTRICITY: SensorDeviceClass.ENERGY,
    ENERGY_TYPE_WATER: SensorDeviceClass.WATER,
    ENERGY_TYPE_GAS: SensorDeviceClass.GAS,
    ENERGY_TYPE_HEAT: SensorDeviceClass.ENERGY,
}

WATER_SUBTYPE_ICON = {
    SUB_TYPE_COLD_WATER: "mdi:snowflake",
    SUB_TYPE_HOT_WATER: "mdi:thermometer-water",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up smart-me sensors from a config entry."""
    coordinator: SmartMeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for device_id, device in coordinator.data.items():
        if device.get("counterReading") is not None:
            entities.append(SmartMeCounterSensor(coordinator, device_id))
        if device.get("activePower") is not None:
            entities.append(SmartMePowerSensor(coordinator, device_id))

    async_add_entities(entities)


class SmartMeEntity(CoordinatorEntity[SmartMeCoordinator]):
    """Base entity tied to one smart-me device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartMeCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def _device(self) -> dict:
        return self.coordinator.data[self._device_id]

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("name") or f"Smart-me {device.get('serial')}",
            manufacturer="smart-me",
            model=str(device.get("serial", "")),
        )


class SmartMeCounterSensor(SmartMeEntity, SensorEntity):
    """Cumulative counter reading (energy / water / gas)."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_translation_key = "counter"

    def __init__(self, coordinator: SmartMeCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_counter"
        self._attr_device_class = ENERGY_TYPE_DEVICE_CLASS.get(
            self._device.get("deviceEnergyType")
        )
        icon = WATER_SUBTYPE_ICON.get(self._device.get("meterSubType"))
        if icon:
            self._attr_icon = icon

    @property
    def native_value(self) -> float | None:
        # Bidirectional meters (e.g. a PV feed-in point) report the general
        # counterReading with a sign indicating flow direction. The Energy
        # dashboard requires a strictly non-negative, ever-increasing total,
        # so prefer the dedicated export counter when present and otherwise
        # fall back to the absolute value.
        value = self._device.get("counterReadingExport")
        if value is None:
            value = self._device.get("counterReading")
        return abs(value) if value is not None else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._device.get("counterReadingUnit")


class SmartMePowerSensor(SmartMeEntity, SensorEntity):
    """Instantaneous power (electricity) or flow rate (water/gas)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "power"

    def __init__(self, coordinator: SmartMeCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_power"
        # Only electricity readings are real "power" in Watts - for water/gas
        # this field is a flow rate, so device_class is left unset there to
        # avoid a unit mismatch with HA's power validation.
        if self._device.get("deviceEnergyType") == ENERGY_TYPE_ELECTRICITY:
            self._attr_device_class = SensorDeviceClass.POWER

    @property
    def native_value(self) -> float | None:
        return self._device.get("activePower")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._device.get("activePowerUnit")
