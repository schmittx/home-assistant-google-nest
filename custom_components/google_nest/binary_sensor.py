"""Support for Google Nest binary sensor entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN
from .entity import GoogleNestCoordinatorEntity, GoogleNestEntity

@dataclass
class GoogleNestBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class to describe a Google Nest binary sensor entity."""

    get_value: Callable[[Any], bool] = lambda value: value
    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    wired_only: bool = False

@dataclass
class GoogleNestBinarySensorCoordinatorEntityDescription(GoogleNestBinarySensorEntityDescription):
    """Class to describe a Google Nest binary sensor coordinator entity."""

    capability: str | None = None
    object_key_prefix: str | None = None

BINARY_SENSOR_DESCRIPTIONS: list[BinarySensorEntityDescription] = [
    GoogleNestBinarySensorEntityDescription(
        key="auto_away",
        name="Occupancy",
        get_value=lambda value: not value,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        entity_category=None,
        wired_only=True,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="battery_health_state",
        name="Battery Health",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="co_status",
        name="CO Status",
        get_value=lambda value: bool(value == 3),
        device_class=BinarySensorDeviceClass.CO,
        entity_category=None,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="dehumidifier_state",
        name="Dehumidifier Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="filter_replacement_needed",
        name="Air Filter Replacement Needed",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="heat_status",
        name="Heat Status",
        get_value=lambda value: bool(value == 3),
        device_class=BinarySensorDeviceClass.HEAT,
        entity_category=None,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="humidifier_state",
        name="Humidifier Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="hvac_ac_state",
        name="Air Conditioner Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="hvac_fan_state",
        name="Fan Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="hvac_heater_state",
        name="Heater Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="ip_address",
        name="Wi-Fi Connection",
        get_value=lambda value: bool(value),
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="line_power_present",
        name="Line Power Present",
        device_class=BinarySensorDeviceClass.POWER,
        wired_only=True,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="smoke_status",
        name="Smoke Status",
        get_value=lambda value: bool(value == 3),
        device_class=BinarySensorDeviceClass.SMOKE,
        entity_category=None,
    ),
    GoogleNestBinarySensorEntityDescription(
        key="wifi_ip_address",
        name="Wi-Fi Connection",
        get_value=lambda value: bool(value),
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
]

BINARY_SENSOR_COORDINATOR_DESCRIPTIONS: list[GoogleNestBinarySensorCoordinatorEntityDescription] = [
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="button_pressed",
        name="Button Pressed",
        entity_category=None,
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="dog_barking_detected",
        name="Dog Barking Detected",
        device_class=BinarySensorDeviceClass.SOUND,
        entity_category=None,
        capability="audio.microphone",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="face_detected",
        name="Face Detected",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        entity_category=None,
        capability="stranger_detection",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="motion_detected",
        name="Motion Detected",
        device_class=BinarySensorDeviceClass.MOTION,
        entity_category=None,
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="package_delivered",
        name="Package Delivered",
        entity_category=None,
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="package_retrieved",
        name="Package Retrieved",
        entity_category=None,
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="person_detected",
        name="Person Detected",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        entity_category=None,
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="person_talking_detected",
        name="Person Talking Detected",
        device_class=BinarySensorDeviceClass.SOUND,
        entity_category=None,
        capability="audio.microphone",
        object_key_prefix="quartz",
    ),
    GoogleNestBinarySensorCoordinatorEntityDescription(
        key="sound_detected",
        name="Sound Detected",
        device_class=BinarySensorDeviceClass.SOUND,
        entity_category=None,
        capability="audio.microphone",
        object_key_prefix="quartz",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest binary sensor entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestBinarySensorEntity | GoogleNestBinarySensorCoordinatorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in BINARY_SENSOR_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):

                if any(
                    [
                        all(
                            [
                                device.object_key.startswith("topaz."),
                                description.wired_only,
                                device.value.get("wired_or_battery") != 0,
                            ]
                        ),
                        all(
                            [
                                key == "dehumidifier_state",
                                not device.value.get("has_dehumidifier"),
                            ]
                        ),
                        all(
                            [
                                key == "humidifier_state",
                                not device.value.get("has_humidifier"),
                            ]
                        ),
                    ]
                ):                
                    continue

                entities.append(
                    GoogleNestBinarySensorEntity(
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
        for description in BINARY_SENSOR_COORDINATOR_DESCRIPTIONS:
            if all(
                [
                    any(
                        [
                            description.capability is None,
                            description.capability in coordinator.data.capabilities,
                        ]
                    ),
                    any(
                        [
                            description.key not in ["dog_barking_detected", "person_talking_detected"],
                            all(
                                [
                                    description.key in ["dog_barking_detected", "person_talking_detected"],
                                    "indoor_chime" not in coordinator.data.capabilities,
                                ]
                            ),
                        ]
                    ),
                    device := data.devices.get(f"{description.object_key_prefix}.{id}"),
                ]
            ):
                entities.append(
                    GoogleNestBinarySensorCoordinatorEntity(
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
        for zone in coordinator.data.zones:
            for description in BINARY_SENSOR_COORDINATOR_DESCRIPTIONS:
                if all(
                    [
                        any(
                            [
                                description.capability is None,
                                description.capability in coordinator.data.capabilities,
                            ]
                        ),
                        device := data.devices.get(f"{description.object_key_prefix}.{id}"),
                        hasattr(zone, description.key),
                    ]
                ):
                    entities.append(
                        GoogleNestBinarySensorCoordinatorEntity(
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
                            zone=zone,
                        )
                    )


    async_add_devices(entities)


class GoogleNestBinarySensorEntity(GoogleNestEntity, BinarySensorEntity):
    """Representation of a Google Nest binary sensor entity."""

    entity_description: GoogleNestBinarySensorEntityDescription

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        state = self.bucket.value.get(self.entity_description.key)
        return self.entity_description.get_value(state)


class GoogleNestBinarySensorCoordinatorEntity(GoogleNestCoordinatorEntity, BinarySensorEntity):
    """Representation of a Google Nest binary sensor coordinator entity."""

    entity_description: GoogleNestBinarySensorCoordinatorEntityDescription

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        if self.zone:
            return getattr(self.zone, self.entity_description.key)
        return getattr(self.device, self.entity_description.key)
