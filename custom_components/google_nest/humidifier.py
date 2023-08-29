"""Support for Google Nest humidifier entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.humidifier import (
    HumidifierAction,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN, LOGGER
from .entity import GoogleNestEntity

@dataclass
class GoogleNestHumidifierEntityDescription(HumidifierEntityDescription):
    """Class to describe a Google Nest humidifier entity."""

    entity_category: str[EntityCategory] | None = None

HUMIDIFIER_DESCRIPTIONS: list[HumidifierEntityDescription] = [
    GoogleNestHumidifierEntityDescription(
        key="has_dehumidifier",
        name="Dehumidifier",
        device_class=HumidifierDeviceClass.DEHUMIDIFIER,
    ),
    GoogleNestHumidifierEntityDescription(
        key="has_humidifier",
        name="Humidifier",
        device_class=HumidifierDeviceClass.HUMIDIFIER,
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest humidifier entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestHumidifierEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in HUMIDIFIER_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):
                if device.value.get(key):
                    entities.append(
                        GoogleNestHumidifierEntity(
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


class GoogleNestHumidifierEntity(GoogleNestEntity, HumidifierEntity):
    """Representation of a Google Nest humidifier entity."""

    entity_description: GoogleNestHumidifierEntityDescription
    _attr_max_humidity: int = 60
    _attr_min_humidity: int = 10
    _attr_humidity_step: int = 5

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self.bucket.value.get("target_humidity_enabled")

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action."""
        if self.is_on:
            if self.bucket.value.get("dehumidifier_state"):
                return HumidifierAction.DRYING
            elif self.bucket.value.get("humidifier_state"):
                return HumidifierAction.HUMIDIFYING
            return HumidifierAction.IDLE
        return HumidifierAction.OFF

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return self.bucket.value.get("current_humidity")

    @property
    def target_humidity(self) -> int | None:
        """Return the humidity we try to reach."""
        return self.bucket.value.get("target_humidity")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    "target_humidity_enabled": True,
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    "target_humidity_enabled": False,
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        humidity = int(round(float(humidity) / self._attr_humidity_step) * self._attr_humidity_step)
        if humidity < self.min_humidity:
            humidity = self.min_humidity
        if humidity > self.max_humidity:
            humidity = self.max_humidity

        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    "target_humidity": humidity,
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)
