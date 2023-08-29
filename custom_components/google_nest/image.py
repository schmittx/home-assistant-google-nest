"""Support for Google Nest image entities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.image import (
    ImageEntity,
    ImageEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import HomeAssistantGoogleNestData
from .api.client import NestClient
from .api.models import Bucket
from .const import DOMAIN, LOGGER
from .entity import GoogleNestEntity

SCAN_INTERVAL = timedelta(minutes=2)

@dataclass
class GoogleNestImageEntityDescription(ImageEntityDescription):
    """Class to describe a Google Nest image entity."""

IMAGE_DESCRIPTIONS: list[GoogleNestImageEntityDescription] = [
    GoogleNestImageEntityDescription(
        key="snapshot_url",
        name="Camera",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest image entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestImageEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in IMAGE_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):
                entities.append(
                    GoogleNestImageEntity(
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
                        hass=hass,
                    )
                )

    async_add_devices(entities, update_before_add=True)


class GoogleNestImageEntity(GoogleNestEntity, ImageEntity):
    """Representation of a Google Nest image entity."""

    _attr_should_poll = True
    entity_description: GoogleNestImageEntityDescription

    def __init__(
        self,
        bucket: Bucket,
        description: GoogleNestImageEntityDescription,
        structures: dict[str, str],
        thermostats: dict[str, str],
        thermostat_device_info: dict[str, dict],
        sensors: dict[str, str],
        areas: dict[str, str],
        swarms: dict[str, str],
        time_zones: dict[str, str],
        client: NestClient,
        hass: HomeAssistant,
    ) -> None:
        """Initialize entity."""
        GoogleNestEntity.__init__(
            self=self,
            bucket=bucket,
            description=description,
            structures=structures,
            thermostats=thermostats,
            thermostat_device_info=thermostat_device_info,
            sensors=sensors,
            areas=areas,
            swarms=swarms,
            time_zones=time_zones,
            client=client,
        )
        ImageEntity.__init__(
            self=self,
            hass=hass,
        )

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        return await self.client.get_camera_snapshot(self.bucket.object_key.split(".")[1])

    @property
    def image_last_updated(self) -> datetime | None:
        """The time when the image was last updated."""
        return self._attr_image_last_updated

    async def async_update(self) -> None:
        """Return bytes of image."""
        self._attr_image_last_updated = dt_util.utcnow()
