"""Support for Google Nest number entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfTime, PERCENTAGE, TEMP_CELSIUS, TIME_HOURS
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN, LOGGER
from .entity import GoogleNestCoordinatorEntity, GoogleNestEntity

@dataclass
class GoogleNestNumberEntityDescription(NumberEntityDescription):
    """Class to describe a Google Nest number entity."""

    mode: str[NumberMode] = NumberMode.AUTO
    get_value: Callable[[Any], bool] = lambda value: value
    set_value: Callable[[Any], bool] = lambda value: value
    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG

@dataclass
class GoogleNestNumberCoordinatorEntityDescription(GoogleNestNumberEntityDescription):
    """Class to describe a Google Nest number coordinator entity."""

    capability: str | None = None
    object_key_prefix: str | None = None

NUMBER_DESCRIPTIONS: list[NumberEntityDescription] = [
    GoogleNestNumberEntityDescription(
        key="max_nighttime_preconditioning_seconds",
        name="Early-On Nighttime Max Duration",
        native_max_value=5,
        native_min_value=0,
        native_step=1,
        get_value=lambda value: (value / 3600),
        set_value=lambda value: int(value * 3600),
        native_unit_of_measurement=TIME_HOURS,
        icon="mdi:timer",
    ),
    GoogleNestNumberEntityDescription(
        key="lower_safety_temp",
        name="Lower Safety Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_max_value=7,
        native_min_value=2,
        native_step=0.5,
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer-chevron-down",
    ),
    GoogleNestNumberEntityDescription(
        key="upper_safety_temp",
        name="Upper Safety Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_max_value=40,
        native_min_value=35,
        native_step=0.5,
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer-chevron-up",
    ),
    GoogleNestNumberEntityDescription(
        key="away_temperature_low",
        name="Lower Eco Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_max_value=21,
        native_min_value=4.5,
        native_step=0.5,
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer-chevron-down",
    ),
    GoogleNestNumberEntityDescription(
        key="away_temperature_high",
        name="Upper Eco Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_max_value=32,
        native_min_value=24.5,
        native_step=0.5,
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer-chevron-up",
    ),
]

NUMBER_COORDINATOR_DESCRIPTIONS: list[GoogleNestNumberCoordinatorEntityDescription] = [
    GoogleNestNumberCoordinatorEntityDescription(
        key="audio.inputgainlevel",
        name="Microphone Sensitivity",
        native_max_value=100,
        native_min_value=0,
        native_step=1,
        get_value=lambda value: int(value * 100),
        set_value=lambda value: value / 100,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:microphone-settings",
        capability="audio.gain",
        object_key_prefix="quartz",
    ),
    GoogleNestNumberCoordinatorEntityDescription(
        key="doorbell.indoor_chime.duration",
        name="Indoor Chime Duration",
        native_max_value=10,
        native_min_value=1,
        native_step=1,
        get_value=lambda value: int(value / 1000),
        set_value=lambda value: int(value * 1000),
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:bell-cog",
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Nest number entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestNumberEntity | GoogleNestNumberCoordinatorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in NUMBER_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):
                entities.append(
                    GoogleNestNumberEntity(
                        bucket=device,
                        description=description,
                        structures=data.structures,
                        thermostats=data.thermostats,
                        thermostat_device_info=data.thermostat_device_info,
                        sensors=data.sensors,
                        areas=data.areas,
                        swarms=data.swarms,
                        time_zones=data.time_zones,
                        client=data.client,
                    )
                )

    for id, coordinator in data.coordinators.items():
        for description in NUMBER_COORDINATOR_DESCRIPTIONS:
            if all(
                [
                    any(
                        [
                            description.capability is None,
                            description.capability in coordinator.data.capabilities,
                        ]
                    ),
                    device := data.devices.get(f"{description.object_key_prefix}.{id}"),
                ]
            ):
                entities.append(
                    GoogleNestNumberCoordinatorEntity(
                        bucket=device,
                        description=description,
                        structures=data.structures,
                        thermostats=data.thermostats,
                        thermostat_device_info=data.thermostat_device_info,
                        sensors=data.sensors,
                        areas=data.areas,
                        swarms=data.swarms,
                        time_zones=data.time_zones,
                        client=data.client,
                        coordinator=coordinator,
                    )
                )

    async_add_devices(entities)


class GoogleNestNumberEntity(GoogleNestEntity, NumberEntity):
    """Representation of a Google Nest number entity."""

    entity_description: GoogleNestNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        state = self.bucket.value.get(self.entity_description.key)
        return self.entity_description.get_value(state)

    async def async_set_value(self, value: float) -> None:
        """Set new value."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    self.entity_description.key: self.entity_description.set_value(value),
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)


class GoogleNestNumberCoordinatorEntity(GoogleNestCoordinatorEntity, NumberEntity):
    """Representation of a Google Nest number coordinator entity."""

    entity_description: GoogleNestNumberCoordinatorEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        value = self.device.properties[self.entity_description.key]
        return self.entity_description.get_value(value)

    async def async_set_value(self, value: float) -> None:
        """Set new value."""
        await self.client.set_camera_property(
            uuid=self.device.uuid,
            key=self.entity_description.key,
            value=self.entity_description.set_value(value),
        )
        await self.coordinator.async_request_refresh()
