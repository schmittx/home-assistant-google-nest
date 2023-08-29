"""Support for Google Nest sensor entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN
from .entity import GoogleNestEntity

@dataclass
class GoogleNestSensorEntityDescription(SensorEntityDescription):
    """Class to describe a Google Nest sensor entity."""

    native_value: Callable[[Any], bool] = lambda value: value
    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    battery_only: bool = False

SENSOR_DESCRIPTIONS: list[GoogleNestSensorEntityDescription] = [
    GoogleNestSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_value=lambda value: value if value <= 100 else None,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        battery_only=True,
    ),
    GoogleNestSensorEntityDescription(
        key="current_humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,
    ),
    GoogleNestSensorEntityDescription(
        key="current_temperature",
        name="Temperature",
        native_value=lambda value: round(value, 1),
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,
    ),
    GoogleNestSensorEntityDescription(
        key="filter_changed_date",
        name="Air Filter Last Changed",
        native_value=lambda value: datetime.datetime.utcfromtimestamp(value),
        device_class=SensorDeviceClass.DATE,
    ),
    GoogleNestSensorEntityDescription(
        key="filter_runtime_sec",
        name="Air Filter Usage",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    GoogleNestSensorEntityDescription(
        key="replace_by_date_utc_secs",
        name="Replace By",
        native_value=lambda value: datetime.datetime.utcfromtimestamp(value),
        device_class=SensorDeviceClass.DATE,
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Nest sensor entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestSensorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SENSOR_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):

                if any(
                    [
                        all(
                            [
                                device.object_key.startswith("topaz."),
                                description.battery_only,
                                device.value.get("wired_or_battery") == 0,
                            ]
                        ),
                        all(
                            [
                                device.object_key.startswith("device."),
                                description.key == "battery_level",
                            ]
                        ),
                    ]
                ):
                    continue

                entities.append(
                    GoogleNestSensorEntity(
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

    async_add_devices(entities)


class GoogleNestSensorEntity(GoogleNestEntity, SensorEntity):
    """Representation of a Google Nest sensor entity."""

    entity_description: GoogleNestSensorEntityDescription

    @property
    def native_value(self) -> bool:
        """Return the state of the sensor."""
        state = self.bucket.value.get(self.entity_description.key)
        return self.entity_description.native_value(state)
