"""Support for Google Nest climate entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantGoogleNestData
from .const import DOMAIN, LOGGER
from .entity import GoogleNestEntity

MODE_TO_PRESET = {
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
    "off": HVACMode.OFF,
    "range": HVACMode.HEAT_COOL,
}

TEMPERATURE_TO_PRESET = {
    "target_temperature": ATTR_TEMPERATURE,
    "target_temperature_high": ATTR_TARGET_TEMP_HIGH,
    "target_temperature_low": ATTR_TARGET_TEMP_LOW,
}

PRESET_TO_MODE = {v: k for k, v in MODE_TO_PRESET.items()}

PRESET_TO_TEMPERATURE = {v: k for k, v in TEMPERATURE_TO_PRESET.items()}

@dataclass
class GoogleNestClimateEntityDescription(ClimateEntityDescription):
    """Class to describe a Google Nest climate entity."""

    entity_category: str[EntityCategory] | None = None

CLIMATE_DESCRIPTIONS: list[ClimateEntityDescription] = [
    GoogleNestClimateEntityDescription(
        key="climate",
        name="Thermostat",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Google Nest climate entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestClimateEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in CLIMATE_DESCRIPTIONS
    }

    for device in data.devices.values():
        if device.object_key.startswith("shared."):
            for description in CLIMATE_DESCRIPTIONS:
                entities.append(
                    GoogleNestClimateEntity(
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


class GoogleNestClimateEntity(GoogleNestEntity, ClimateEntity):
    """Representation of a Google Nest climate entity."""

    entity_description: GoogleNestClimateEntityDescription
    _attr_hvac_modes: list[HVACMode] | list[str] = [*PRESET_TO_MODE]
    _attr_supported_features: int = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.TURN_OFF |
        ClimateEntityFeature.TURN_ON
    )
    _attr_temperature_unit: str = UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.bucket.value.get("current_temperature")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self.bucket.value.get("target_temperature")

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach.

        Requires ClimateEntityFeature.TARGET_TEMPERATURE_RANGE.
        """
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self.bucket.value.get("target_temperature_high")
        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach.

        Requires ClimateEntityFeature.TARGET_TEMPERATURE_RANGE.
        """
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self.bucket.value.get("target_temperature_low")
        return None

    @property
    def hvac_action(self) -> HVACAction | str | None:
        """Return the current running hvac operation if supported."""
        if self.bucket.value.get("target_temperature_type") == "off":
            return HVACAction.OFF
        else:
            if self.bucket.value.get("hvac_heater_state"):
                return HVACAction.HEATING
            if self.bucket.value.get("hvac_ac_state"):
                return HVACAction.COOLING
            return HVACAction.IDLE

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        """Return hvac operation ie. heat, cool mode."""
        hvac_mode = self.bucket.value.get("target_temperature_type")
        return MODE_TO_PRESET.get(hvac_mode)

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        if self.bucket.value.get("can_cool") and self.bucket.value.get("can_heat"):
            return self._attr_supported_features | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        return self._attr_supported_features

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    "target_temperature_type": PRESET_TO_MODE[hvac_mode],
                },
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        value = {}
        for k, v in PRESET_TO_TEMPERATURE.items():
            if temp := kwargs.get(k):
                value[v] = temp
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": value,
            }
        ]
        result = await self.client.update_objects(objects)
        LOGGER.debug(result)
