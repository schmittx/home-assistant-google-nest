"""Support for Google Nest switch entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN, LOGGER
from .entity import GoogleNestCoordinatorEntity, GoogleNestEntity

BRIGHTNESS_TO_PRESET: dict[str, str] = {1: "low", 2: "medium", 3: "high"}
PRESET_TO_BRIGHTNESS = {v: k for k, v in BRIGHTNESS_TO_PRESET.items()}

@dataclass
class GoogleNestSwitchEntityDescription(SwitchEntityDescription):
    """Class to describe a Google Nest switch entity."""

    get_value: Callable[[Any], bool] = lambda value: value
    set_value: Callable[[Any], bool] = lambda value: value
    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG

@dataclass
class GoogleNestSwitchCoordinatorEntityDescription(GoogleNestSwitchEntityDescription):
    """Class to describe a Google Nest switch coordinator entity."""

    capability: str | None = None
    object_key_prefix: str | None = None

SWITCH_DESCRIPTIONS: list[GoogleNestSwitchEntityDescription] = [
    GoogleNestSwitchEntityDescription(
        key="ntp_green_led_enable",
        name="Nightly Promise",
        icon="mdi:weather-night",
    ),
    GoogleNestSwitchEntityDescription(
        key="heads_up_enable",
        name="Heads-Up",
        icon="mdi:message-alert",
    ),
    GoogleNestSwitchEntityDescription(
        key="steam_detection_enable",
        name="Steam Check",
        icon="mdi:weather-rainy",
    ),
    GoogleNestSwitchEntityDescription(
        key="away",
        name="Away",
        entity_category=None,
        icon="mdi:home-outline",
    ),
    GoogleNestSwitchEntityDescription(
        key="hvac_safety_shutoff_enabled",
        name="Emergency Shutoff CO",
        icon="mdi:smoke-detector",
    ),
    GoogleNestSwitchEntityDescription(
        key="hvac_smoke_safety_shutoff_enabled",
        name="Emergency Shutoff Smoke",
        icon="mdi:smoke-detector-variant",
    ),
    GoogleNestSwitchEntityDescription(
        key="phone_hush_enable",
        name="Silencing Alarms",
        icon="mdi:cellphone-sound",
    ),
    GoogleNestSwitchEntityDescription(
        key="home_away_input",
        name="Home/Away Assist",
        icon="mdi:motion-sensor",
    ),
    GoogleNestSwitchEntityDescription(
        key="audio_self_test_enabled",
        name="Sound Check",
        icon="mdi:speaker",
    ),
    GoogleNestSwitchEntityDescription(
        key="audio_self_test_notify",
        name="Sound Check Notification",
        icon="mdi:speaker-message",
    ),
    GoogleNestSwitchEntityDescription(
        key="sunlight_correction_enabled",
        name="Sunblock",
        icon="mdi:sun-thermometer",
    ),
    GoogleNestSwitchEntityDescription(
        key="preconditioning_enabled",
        name="Early-On",
        icon="mdi:sun-clock",
    ),
    GoogleNestSwitchEntityDescription(
        key="fan_cooling_enabled",
        name="Airwave",
        icon="mdi:weather-windy",
    ),
    GoogleNestSwitchEntityDescription(
        key="auto_dehum_enabled",
        name="Cool to Dry",
        icon="mdi:water",
    ),
    GoogleNestSwitchEntityDescription(
        key="learning_mode",
        name="Auto-Schedule",
        icon="mdi:calendar",
    ),
    GoogleNestSwitchEntityDescription(
        key="auto_away_enable",
        name="Away Eco Temperatures",
        icon="mdi:home-thermometer",
    ),
    GoogleNestSwitchEntityDescription(
        key="filter_reminder_enabled",
        name="Air Filter Reminder",
        icon="mdi:air-filter",
    ),
    GoogleNestSwitchEntityDescription(
        key="lower_safety_temp_enabled",
        name="Lower Safety Temperature",
        icon="mdi:thermometer-chevron-down",
    ),
    GoogleNestSwitchEntityDescription(
        key="upper_safety_temp_enabled",
        name="Upper Safety Temperature",
        icon="mdi:thermometer-chevron-up",
    ),
    GoogleNestSwitchEntityDescription(
        key="away_temperature_low_enabled",
        name="Lower Eco Temperature",
        icon="mdi:thermometer-chevron-down",
    ),
    GoogleNestSwitchEntityDescription(
        key="away_temperature_high_enabled",
        name="Upper Eco Temperature",
        icon="mdi:thermometer-chevron-up",
    ),
    GoogleNestSwitchEntityDescription(
        key="rcs_control_setting",
        name="Sensor Schedule",
        get_value=lambda value: bool(value == "SCHEDULE"),
        set_value=lambda value: "SCHEDULE" if value else "OFF",
        icon="mdi:calendar",
    ),
    GoogleNestSwitchEntityDescription(
        key="streaming_state",
        name="Camera On/Off",
        get_value=lambda value: bool(value == "streaming-enabled"),
        set_value=lambda value: "streaming-enabled" if value else "streaming-disabled",
        icon="mdi:video",
    ),
    GoogleNestSwitchEntityDescription(
        key="audio_input_enabled",
        name="Microphone",
        icon="mdi:microphone",
    ),
    GoogleNestSwitchEntityDescription(
        key="humidity_control_lockout_enabled",
        name="Quiet Time",
        icon="mdi:air-humidifier-off",
    ),
]

SWITCH_COORDINATOR_DESCRIPTIONS: list[GoogleNestSwitchCoordinatorEntityDescription] = [
    GoogleNestSwitchCoordinatorEntityDescription(
        key="audio.recording.enabled",
        name="Audio Recording",
        icon="mdi:record-rec",
        capability="audio.microphone",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="audio.start-stop-sound",
        name="Talk & Listen Tone",
        icon="mdi:microphone-message",
        get_value=lambda value: bool(value == 1),
        set_value=lambda value: 1 if value else 0,
        capability="talkback.chime.on_off",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="cvr.allowed",
        name="Video Recording",
        icon="mdi:record-rec",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="doorbell.chime_assist.enabled",
        name="Visitor Announcements",
        icon="mdi:speaker-message",
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="doorbell.indoor_chime.enabled",
        name="Indoor Chime",
        icon="mdi:bell-ring",
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="nest.away.streaming.enabled",
        name="Home/Away Assist",
        icon="mdi:video-marker",
        capability="streaming.start-stop",
        object_key_prefix="quartz",
    ),
    GoogleNestSwitchCoordinatorEntityDescription(
        key="video.flipped",
        name="Rotate Image",
        icon="mdi:camera-flip",
        capability="video.flip",
        object_key_prefix="quartz",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest switch entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestSwitchEntity | GoogleNestSwitchCoordinatorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SWITCH_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if all(
                [
                    description := SUPPORTED_KEYS.get(key),
                    any(
                        [
                            key != "humidity_control_lockout_enabled",
                            all(
                                [
                                    key == "humidity_control_lockout_enabled",
                                    any(
                                        [
                                            device.value.get("has_dehumidifier"),
                                            device.value.get("has_humidifier"),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ):
                entities.append(
                    GoogleNestSwitchEntity(
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
        for description in SWITCH_COORDINATOR_DESCRIPTIONS:
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
                    GoogleNestSwitchCoordinatorEntity(
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


class GoogleNestSwitchEntity(GoogleNestEntity, SwitchEntity):
    """Representation of a Google Nest switch entity."""

    entity_description: GoogleNestSwitchEntityDescription

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.entity_description.key == "humidity_control_lockout_enabled":
            if self.bucket.value.get("has_dehumidifier"):
                return f"{self.device_name} Dehumidifier {self.entity_description.name}"
            if self.bucket.value.get("has_humidifier"):
                return f"{self.device_name} Humidifier {self.entity_description.name}"
        return super().name

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        state = self.bucket.value.get(self.entity_description.key)
        return self.entity_description.get_value(state)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    self.entity_description.key: self.entity_description.set_value(True),
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
                    self.entity_description.key: self.entity_description.set_value(False),
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)


class GoogleNestSwitchCoordinatorEntity(GoogleNestCoordinatorEntity, SwitchEntity):
    """Representation of a Google Nest switch coordinator entity."""

    entity_description: GoogleNestSwitchCoordinatorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        value = self.device.properties[self.entity_description.key]
        return self.entity_description.get_value(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.client.set_camera_property(
            uuid=self.device.uuid,
            key=self.entity_description.key,
            value=self.entity_description.set_value(True),
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.client.set_camera_property(
            uuid=self.device.uuid,
            key=self.entity_description.key,
            value=self.entity_description.set_value(False),
        )
        await self.coordinator.async_request_refresh()
