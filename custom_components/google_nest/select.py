"""Support for Google Nest select entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN, LOGGER
from .entity import GoogleNestCoordinatorEntity, GoogleNestEntity

_LOGGER = logging.getLogger(__name__)

BRIGHTNESS_TO_PRESET: dict[int, str] = {1: "low", 2: "medium", 3: "high"}
PRESET_TO_BRIGHTNESS: dict[str, int]= {v: k for k, v in BRIGHTNESS_TO_PRESET.items()}

PRESET_TO_ENABLE: dict[str, dict[str, bool]] = {
    "off": {
        "night_light_continuous": False,
        "night_light_enable": False,
    },
    "on": {
        "night_light_continuous": False,
        "night_light_enable": True,
    },
    "always_on": {
        "night_light_continuous": True,
        "night_light_enable": True,
    },
}

SCALE_TO_PRESET: dict[str, str] = {"C": "c", "F": "f"}
PRESET_TO_SCALE = {v: k for k, v in SCALE_TO_PRESET.items()}

TIME_INTERVALS: dict[str, str] = {
    "morning": (25200, 39600), # 7am (39600) - 11am (54000)
    "midday": (39600, 57600), # 11am (54000) - 4pm (72000)
    "evening": (57600, 75600), # 4pm (72000) - 9pm (3600)
    "night": (75600, 25200), # 9pm (3600) - 7am (25200)
}

STATUS_LED_BRIGHTNESS_TO_PRESET: dict[int, str] = {0: "auto", 1: "low", 2: "high"}
PRESET_TO_STATUS_LED_BRIGHTNESS: dict[str, int] = {v: k for k, v in STATUS_LED_BRIGHTNESS_TO_PRESET.items()}

IR_LED_STATE_TO_PRESET: dict[str, str] = {"always_off": "off", "auto_on": "auto", "always_on": "always_on"}
PRESET_TO_IR_LED_STATE: dict[str, str] = {v: k for k, v in IR_LED_STATE_TO_PRESET.items()}

DATA_USAGE_CAPABILITY_TO_PRESET = {
    "streaming.data-usage-tier.30": "30_gb_month",
    "streaming.data-usage-tier.100": "100_gb_month",
    "streaming.data-usage-tier.120": "120_gb_month",
    "streaming.data-usage-tier.200": "200_gb_month",
    "streaming.data-usage-tier.300": "300_gb_month",
    "streaming.data-usage-tier.400": "400_gb_month",
}
PRESET_TO_DATA_USAGE_CAPABILITY: dict[str, int] = {v: k for k, v in DATA_USAGE_CAPABILITY_TO_PRESET.items()}

DATA_USAGE_TIER_TO_PRESET: dict[int, str] = {
    30: "30_gb_month",
    100: "100_gb_month",
    120: "120_gb_month",
    200: "200_gb_month",
    300: "300_gb_month",
    400: "400_gb_month",
}
PRESET_TO_DATA_USAGE_TIER: dict[str, int] = {v: k for k, v in DATA_USAGE_TIER_TO_PRESET.items()}

HUMIDITY_CONTROL_LOCKOUT_TO_PRESET: dict[int, str] = {
    0: "12_am",
    3600: "1_am",
    7200: "2_am",
    10800: "3_am",
    14400: "4_am",
    18000: "5_am",
    21600: "6_am",
    25200: "7_am",
    28800: "8_am",
    32400: "9_am",
    36000: "10_am",
    39600: "11_am",
    43200: "12_pm",
    46800: "1_pm",
    50400: "2_pm",
    54000: "3_pm",
    57600: "4_pm",
    61200: "5_pm",
    64800: "6_pm",
    68400: "7_pm",
    72000: "8_pm",
    75600: "9_pm",
    79200: "10_pm",
    82800: "11_pm",
}
PRESET_TO_HUMIDITY_CONTROL_LOCK: dict[str, int] = {v: k for k, v in HUMIDITY_CONTROL_LOCKOUT_TO_PRESET.items()}

AWAY_STATUS_TO_PRESET: dict[bool, str] = {
    True: "away",
    False: "home",
}
PRESET_TO_AWAY_STATUS: dict[str, bool] = {v: k for k, v in AWAY_STATUS_TO_PRESET.items()}

@dataclass
class GoogleNestSelectEntityDescription(SelectEntityDescription):
    """Class to describe a Google Nest select entity."""

    options: list[str] | None = None
    get_value: Callable[[Any], bool] = lambda value: value
    set_value: Callable[[Any], bool] = lambda value: value
    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG
    translation_key: str | None = "all"

@dataclass
class GoogleNestSelectCoordinatorEntityDescription(GoogleNestSelectEntityDescription):
    """Class to describe a Google Nest select coordinator entity."""

    capability: str | None = None
    object_key_prefix: str | None = None

SELECT_DESCRIPTIONS: list[GoogleNestSelectEntityDescription] = [
    GoogleNestSelectEntityDescription(
        key="active_rcs_sensors",
        name="Active Sensor",
        entity_category=None,
        icon="mdi:access-point",
    ),
    GoogleNestSelectEntityDescription(
        key="audio_self_test_start_utc_offset_secs",
        name="Sound Check Preferred Time",
        options=[*TIME_INTERVALS],
        icon="mdi:clock-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="away",
        name="status",
        options=[*PRESET_TO_AWAY_STATUS],
        get_value=lambda value: AWAY_STATUS_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_AWAY_STATUS.get(value),
        icon="mdi:home-switch-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="humidity_control_lockout_end_time",
        name="Quiet Time End",
        options=[*PRESET_TO_HUMIDITY_CONTROL_LOCK],
        get_value=lambda value: HUMIDITY_CONTROL_LOCKOUT_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_HUMIDITY_CONTROL_LOCK.get(value),
        icon="mdi:clock-end",
    ),
    GoogleNestSelectEntityDescription(
        key="humidity_control_lockout_start_time",
        name="Quiet Time Start",
        options=[*PRESET_TO_HUMIDITY_CONTROL_LOCK],
        get_value=lambda value: HUMIDITY_CONTROL_LOCKOUT_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_HUMIDITY_CONTROL_LOCK.get(value),
        icon="mdi:clock-start",
    ),
    GoogleNestSelectEntityDescription(
        key="night_light_brightness",
        name="Brightness",
        options=[*PRESET_TO_BRIGHTNESS],
        get_value=lambda value: BRIGHTNESS_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_BRIGHTNESS.get(value),
        icon="mdi:lightbulb-on",
    ),
    GoogleNestSelectEntityDescription(
        key="night_light_enable",
        name="Pathlight",
        options=[*PRESET_TO_ENABLE],
        icon="mdi:lightbulb-night",
    ),
    GoogleNestSelectEntityDescription(
        key="sensor_schedule_evening",
        name="Sensor Schedule Evening",
        icon="mdi:clock-time-four-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="sensor_schedule_midday",
        name="Sensor Schedule Midday",
        icon="mdi:clock-time-eleven-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="sensor_schedule_morning",
        name="Sensor Schedule Morning",
        icon="mdi:clock-time-seven-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="sensor_schedule_night",
        name="Sensor Schedule Night",
        icon="mdi:clock-time-nine-outline",
    ),
    GoogleNestSelectEntityDescription(
        key="temperature_scale",
        name="Temperature Units",
        options=[*PRESET_TO_SCALE],
        get_value=lambda value: SCALE_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_SCALE.get(value),
        icon="mdi:thermometer-lines",
    ),
]

SELECT_COORDINATOR_DESCRIPTIONS: list[GoogleNestSelectCoordinatorEntityDescription] = [
    GoogleNestSelectCoordinatorEntityDescription(
        key="doorbell.indoor_chime.type",
        name="Indoor Chime Type",
        options=["electronic", "mechanical"],
        icon="mdi:bell-cog",
        capability="indoor_chime",
        object_key_prefix="quartz",
    ),
    GoogleNestSelectCoordinatorEntityDescription(
        key="irled.state",
        name="Night Vision",
        options=[*PRESET_TO_IR_LED_STATE],
        get_value=lambda value: IR_LED_STATE_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_IR_LED_STATE.get(value),
        icon="mdi:lightbulb-night",
        capability="irled",
        object_key_prefix="quartz",
    ),
    GoogleNestSelectCoordinatorEntityDescription(
        key="statusled.brightness",
        name="Status Light",
        options=[*PRESET_TO_STATUS_LED_BRIGHTNESS],
        get_value=lambda value: STATUS_LED_BRIGHTNESS_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_STATUS_LED_BRIGHTNESS.get(value),
        icon="mdi:lightbulb-on",
        capability="statusled.brightness.settable",
        object_key_prefix="quartz",
    ),
    GoogleNestSelectCoordinatorEntityDescription(
        key="streaming.data-usage-tier",
        name="Quality & Bandwidth",
        options=None,
        get_value=lambda value: DATA_USAGE_TIER_TO_PRESET.get(value),
        set_value=lambda value: PRESET_TO_DATA_USAGE_TIER.get(value),
        icon="mdi:filmstrip",
        object_key_prefix="quartz",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest select entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestSelectEntity | GoogleNestSelectCoordinatorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SELECT_DESCRIPTIONS
    }
    SENSOR_SCHEDULE_KEYS = {
        description.key: description for description in SELECT_DESCRIPTIONS if description.key.startswith("sensor_schedule")
    }

    for device in data.devices.values():
        for key in device.value:
            if all(
                [
                    description := SUPPORTED_KEYS.get(key),
                    any(
                        [
                            not key.startswith("humidity_control_lockout"),
                            all(
                                [
                                    key.startswith("humidity_control_lockout"),
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
                    GoogleNestSelectEntity(
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
            elif key == "sensor_schedule":
                for description in SENSOR_SCHEDULE_KEYS.values():
                    entities.append(
                        GoogleNestSelectEntity(
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
        for description in SELECT_COORDINATOR_DESCRIPTIONS:
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
                    GoogleNestSelectCoordinatorEntity(
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


class GoogleNestSelectEntity(GoogleNestEntity, SelectEntity):
    """Representation of a Google Nest select entity."""

    entity_description: GoogleNestSelectEntityDescription

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.entity_description.key.startswith("humidity_control_lockout"):
            if self.bucket.value.get("has_dehumidifier"):
                return f"{self.device_name} Dehumidifier {self.entity_description.name}"
            if self.bucket.value.get("has_humidifier"):
                return f"{self.device_name} Humidifier {self.entity_description.name}"
        return super().name

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the entity state."""
        if self.entity_description.key == "audio_self_test_start_utc_offset_secs":
            time_zone = ZoneInfo(self.time_zones[self.bucket.object_key.split(".")[1]])
            offset = time_zone.utcoffset(datetime.datetime.now()).total_seconds()
            start = self.bucket.value["audio_self_test_start_utc_offset_secs"]
            end = self.bucket.value["audio_self_test_end_utc_offset_secs"]
            for key, value in TIME_INTERVALS.items():
                utc_start = value[0] - offset
                if utc_start >= 86400:
                    utc_start = utc_start - 86400
                utc_end = value[1] - offset
                if utc_end >= 86400:
                    utc_end = utc_end - 86400
                if (start, end) == (utc_start, utc_end):
                    return key
            return "unknown"

        elif self.entity_description.key.startswith("sensor_schedule"):
            intervals = self.bucket.value["sensor_schedule"]["intervals"]
            for key, value in TIME_INTERVALS.items():
                if self.entity_description.key.endswith(key):
                    for interval in intervals:
                        if interval["end_time"] == value[1]:
                            sensors = interval["sensors"]
            return self.sensors.get(sensors[0], self.area_name)

        else:
            state = self.bucket.value[self.entity_description.key]

            if self.entity_description.key == "active_rcs_sensors":
                return self.sensors[state[0]] if state else self.area_name

            elif self.entity_description.key == "night_light_enable":
                value = {
                    "night_light_continuous": self.bucket.value["night_light_continuous"],
                    "night_light_enable": state,
                }
                for preset, data in PRESET_TO_ENABLE.items():
                    if value == data:
                        return preset

            get_value = self.entity_description.get_value
            return get_value(state)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        if options := self.entity_description.options:
            return options
#        LOGGER.debug(f"Entity: {self.name} has 'self.sensors': {self.sensors}")
        options = [self.sensors[key] for key in self.bucket.value["associated_rcs_sensors"]]
        options.append(self.area_name)
        return sorted(options)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.entity_description.key == "active_rcs_sensors":
            if option == self.area_name:
                payload = []
            else:
                for key, where_name in self.sensors.items():
                    if where_name == option:
                        payload = [key]
            value = {
                self.entity_description.key: payload
            }

        elif self.entity_description.key.startswith("sensor_schedule"):
            sensor_schedule = self.bucket.value["sensor_schedule"]
            for key, value in TIME_INTERVALS.items():
                if self.entity_description.key.endswith(key):
                    for interval in sensor_schedule["intervals"]:
                        if interval["end_time"] == value[1]:
                            if option == self.area_name:
                                payload = [""]
                            else:
                                for object_key, where_name in self.sensors.items():
                                    if where_name == option:
                                        payload = [object_key]
                            interval["sensors"] = payload
            value = {
                "sensor_schedule": sensor_schedule
            }

        elif self.entity_description.key == "night_light_enable":
            value = PRESET_TO_ENABLE[option]

        elif self.entity_description.key == "audio_self_test_start_utc_offset_secs":
            time_zone = ZoneInfo(self.time_zones[self.bucket.object_key.split(".")[1]])
            offset = time_zone.utcoffset(datetime.datetime.now()).total_seconds()
            start = int(TIME_INTERVALS[option][0] - offset)
            if start >= 86400:
                start = start - 86400
            end = int(TIME_INTERVALS[option][1] - offset)
            if end >= 86400:
                end = end - 86400
            value = {
                "audio_self_test_start_utc_offset_secs": start,
                "audio_self_test_end_utc_offset_secs": end,
            }

        else:
            value = {
                self.entity_description.key: self.entity_description.set_value(option)
            }

        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": value,
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)


class GoogleNestSelectCoordinatorEntity(GoogleNestCoordinatorEntity, SelectEntity):
    """Representation of a Google Nest select coordinator entity."""

    entity_description: GoogleNestSelectCoordinatorEntityDescription

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the entity state."""
        value = self.device.properties[self.entity_description.key]
        return self.entity_description.get_value(value)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        if options := self.entity_description.options:
            return options
        options = []
        for preset, tier in PRESET_TO_DATA_USAGE_CAPABILITY.items():
            if tier in self.device.capabilities:
                options.append(preset)
        return options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.client.set_camera_property(
            uuid=self.device.uuid,
            key=self.entity_description.key,
            value=self.entity_description.set_value(option),
        )
        await self.coordinator.async_request_refresh()
