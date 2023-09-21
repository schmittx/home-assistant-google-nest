"""Support for Google Nest entities."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, LOGGER
from .api.client import NestClient
from .api.models import Bucket, Camera as NestCamera, Zone as NestCameraZone

PROTECT_MODEL_MAP = {
    "Topaz-2.7": "2nd Gen",
}

THERMOSTAT_MODEL_MAP = {
    "Display-3.4": "Nest Learning Thermostat 3rd Gen",
}


class GoogleNestEntity(Entity):
    """Class to describe a Google Nest entity and link it to a device."""

    _attr_should_poll = False

    def __init__(
        self,
        bucket: Bucket,
        description: EntityDescription,
        structures: dict[str, str],
        thermostats: dict[str, str],
        thermostat_device_info: dict[str, dict],
        sensors: dict[str, str],
        areas: dict[str, str],
        swarms: dict[str, str],
        time_zones: dict[str, str],
        client: NestClient,
    ) -> None:
        """Initialize."""
        self.bucket = bucket
        self.client = client
        self.thermostat_device_info = thermostat_device_info.get(bucket.object_key.split(".")[1])
        self.entity_description = description
        self.sensors = {key: areas.get(where_id) for key, where_id in sensors.items()}
        self.structure_name = structures.get(bucket.object_key.split(".")[1])
        self.swarms = swarms
        self.time_zones = time_zones
        self.where_id = bucket.value.get("where_id", thermostats.get(bucket.object_key.split(".")[1]))

        self.area_name = areas.get(self.where_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        if self.bucket.object_key.startswith("kryptonite."):
            return DeviceInfo(
                identifiers={(DOMAIN, self.bucket.value["serial_number"])},
                name=self.device_name,
                manufacturer="Google Nest",
                model="Temperature Sensor",
                suggested_area=self.area_name,
                via_device=(DOMAIN, self.swarms[self.bucket.object_key.split(".")[1]]),
            )

        if any(
            [
                self.bucket.object_key.startswith("safety."),
                self.bucket.object_key.startswith("structure."),
            ]
        ):
            return DeviceInfo(
                identifiers={(DOMAIN, self.bucket.object_key.split(".")[1])},
                name=self.device_name,
                manufacturer="Google Nest",
                model="Structure",
                entry_type=DeviceEntryType.SERVICE,
            )

        if any(
            [
                self.bucket.object_key.startswith("device."),
                self.bucket.object_key.startswith("link."),
                self.bucket.object_key.startswith("rcs_settings."),
                self.bucket.object_key.startswith("shared."),
                self.bucket.object_key.startswith("track."),
            ]
        ):
            return DeviceInfo(
                identifiers={(DOMAIN, self.bucket.object_key.split(".")[1])},
                name=self.device_name,
                manufacturer="Google Nest",
                model="Thermostat",
                hw_version=THERMOSTAT_MODEL_MAP.get(self.thermostat_device_info["model_version"]),
                sw_version=self.thermostat_device_info["current_version"],
                suggested_area=self.area_name,
                via_device=(DOMAIN, self.swarms[self.bucket.object_key.split(".")[1]]),
            )

        if self.bucket.object_key.startswith("quartz."):
            return DeviceInfo(
                connections={
                    (dr.CONNECTION_NETWORK_MAC, self.bucket.value["mac_address"])
                },
                identifiers={(DOMAIN, self.bucket.value["serial_number"])},
                name=self.device_name,
                manufacturer="Google Nest",
                model="Camera",
                hw_version=self.bucket.value["model"].title(),
                sw_version=self.bucket.value["software_version"],
                suggested_area=self.area_name,
                via_device=(DOMAIN, self.bucket.value["structure_id"]),
            )

        if self.bucket.object_key.startswith("topaz."):
            hw_version = "Wired" if self.bucket.value["wired_or_battery"] == 0 else "Battery-Powered"
            if model := PROTECT_MODEL_MAP.get(self.bucket.value["model"]):
                hw_version = f"{hw_version} {model}"
            return DeviceInfo(
                connections={
                    (dr.CONNECTION_NETWORK_MAC, self.bucket.value["wifi_mac_address"])
                },
                identifiers={(DOMAIN, self.bucket.value["serial_number"])},
                name=self.device_name,
                manufacturer="Google Nest",
                model="Protect",
                hw_version=hw_version,
                sw_version=self.bucket.value["software_version"],
                suggested_area=self.area_name,
                via_device=(DOMAIN, self.bucket.value["structure_id"]),
            )

        return None

    @property
    def device_name(self) -> str:
        """Return the name of the device."""
        if description := self.bucket.value.get("description"):
            return description
        if name := self.bucket.value.get("name"):
            return name
        if self.area_name:
            return self.area_name
        if label := self.bucket.value.get("description"):
            return label
        return self.structure_name

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if description := self.entity_description.name:
            return f"{self.device_name} {description}"
        return self.device_name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.bucket.object_key}-{self.entity_description.key}"

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.bucket.object_key, self.update_callback
            )
        )

    @callback
    def update_callback(self, bucket: Bucket):
        """Update the entities state."""
        self.bucket = bucket
        self.async_write_ha_state()


class GoogleNestCoordinatorEntity(GoogleNestEntity, CoordinatorEntity):
    """Class to describe a Google Nest entity and link it to a device."""

    def __init__(
        self,
        bucket: Bucket,
        description: EntityDescription,
        structures: dict[str, str],
        thermostats: dict[str, str],
        thermostat_device_info: dict[str, dict],
        sensors: dict[str, str],
        areas: dict[str, str],
        swarms: dict[str, str],
        time_zones: dict[str, str],
        client: NestClient,
        coordinator: DataUpdateCoordinator,
        zone: NestCameraZone = None,
    ) -> None:
        """Initialize."""
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
        CoordinatorEntity.__init__(
            self=self,
            coordinator=coordinator,
        )
        self.zone = zone

    @property
    def device(self) -> NestCamera | None:
        """Return a NestCamera object."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return all(
            [
                self.coordinator.last_update_success,
                self.device.is_connected,
            ]
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.zone:
            return f"{self.device_name} {self.zone.name} {self.entity_description.name}"
        return super().name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.zone:
            return f"{self.bucket.object_key}-{self.zone.id}-{self.entity_description.key}"
        return super().unique_id

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await GoogleNestEntity.async_added_to_hass(self)
        await CoordinatorEntity.async_added_to_hass(self)


@dataclass(slots=True)
class NestCoordinatorEntityDescription:
    """A class that describes Home Assistant entities."""

    capability: str | None = None
    object_key_prefix: str | None = None
