"""Support for Google Nest weather entities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import time

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_WINDY_VARIANT,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_TIME,
    Forecast,
    WeatherEntity,
    WeatherEntityDescription,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfSpeed, UnitOfTemperature

from . import HomeAssistantGoogleNestData
from .api.client import NestClient
from .api.models import Bucket
from .const import DOMAIN
from .entity import GoogleNestEntity

CONDITION_MAP = {
    "Chance of Rain": ATTR_CONDITION_RAINY,
    "Chance of Snow": ATTR_CONDITION_SNOWY,
    "Chance of Thunderstorms": ATTR_CONDITION_LIGHTNING_RAINY,
    "Clear": ATTR_CONDITION_SUNNY,
    "Clear Night": ATTR_CONDITION_CLEAR_NIGHT,
    "Cloudy": ATTR_CONDITION_CLOUDY,
    "Exceptional": ATTR_CONDITION_EXCEPTIONAL,
    "Fog": ATTR_CONDITION_FOG,
    "Hail": ATTR_CONDITION_HAIL,
    "Lightning": ATTR_CONDITION_LIGHTNING,
    "Lightning Rainy": ATTR_CONDITION_LIGHTNING_RAINY,
    "Mostly Cloudy": ATTR_CONDITION_CLOUDY,
    "Partly Cloudy": ATTR_CONDITION_PARTLYCLOUDY,
    "Pouring": ATTR_CONDITION_POURING,
    "Rain": ATTR_CONDITION_RAINY,
    "Rainy": ATTR_CONDITION_RAINY,
    "Sleet": ATTR_CONDITION_SNOWY_RAINY,
    "Snow": ATTR_CONDITION_SNOWY,
    "Snowy": ATTR_CONDITION_SNOWY,
    "Snowy Rainy": ATTR_CONDITION_SNOWY_RAINY,
    "Sunny": ATTR_CONDITION_SUNNY,
    "Thunderstorms": ATTR_CONDITION_LIGHTNING_RAINY,
    "Mostly Sunny": ATTR_CONDITION_SUNNY,
    "Windy": ATTR_CONDITION_WINDY,
    "Windy Variant": ATTR_CONDITION_WINDY_VARIANT,
}

SCAN_INTERVAL = timedelta(minutes=10)

@dataclass
class GoogleNestWeatherEntityDescription(WeatherEntityDescription):
    """Class to describe a Google Nest weather entity."""

WEATHER_DESCRIPTIONS: list[GoogleNestWeatherEntityDescription] = [
    GoogleNestWeatherEntityDescription(
        key="postal_code",
        name="Weather",
    ),
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Nest weather entity based on a config entry."""

    data: HomeAssistantGoogleNestData = hass.data[DOMAIN][entry.entry_id]
    entities: list[GoogleNestWeatherEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in WEATHER_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if (description := SUPPORTED_KEYS.get(key)) and device.object_key.startswith("structure."):
                entities.append(
                    GoogleNestWeatherEntity(
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

    async_add_devices(entities, update_before_add=True)


class GoogleNestWeatherEntity(GoogleNestEntity, WeatherEntity):
    """Representation of a Google Nest weather entity."""

    entity_description: GoogleNestWeatherEntityDescription
    _attr_native_temperature_unit: str | None = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit: str | None = UnitOfSpeed.MILES_PER_HOUR
    _attr_should_poll = True
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        bucket: Bucket,
        description: GoogleNestWeatherEntityDescription,
        structures: dict[str, str],
        thermostats: dict[str, str],
        thermostat_device_info: dict[str, dict],
        sensors: dict[str, str],
        areas: dict[str, str],
        swarms: dict[str, str],
        time_zones: dict[str, str],
        client: NestClient,
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
        self._data = {}
        self._forecast_listeners = {"daily": [], "hourly": [], "twice_daily": []}

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self._forecast.daily

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self._forecast.hourly

    async def async_update(self) -> None:
        """Return bytes of camera image."""
        self._data = await self.client.get_weather(
            int(self.bucket.value.get(self.entity_description.key)),
        )
        await self.async_update_listeners(("daily", "hourly"))

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if condition := self._data.get("current", {}).get("condition"):
            if condition not in CONDITION_MAP.keys():
                _LOGGER.debug(f'Found unmapped weather condition - {condition}')
            if condition == "Clear" and not self._is_sun_up:
                condition = "Clear Night"
            return CONDITION_MAP.get(condition, condition)
        return None

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature in native units."""
        return self._data.get("current", {}).get("temp_c")

    @property
    def humidity(self) -> float | None:
        """Return the humidity in native units."""
        return self._data.get("current", {}).get("humidity")

    @property
    def native_wind_speed(self) -> float | None:
        return self._data.get("current", {}).get("wind_mph")

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        return self._data.get("current", {}).get("wind_dir")

    @property
    def _forecast(self) -> GoogleNestWeatherForecast:
        """Return the forecast in native units."""
        return GoogleNestWeatherForecast(self._data)

    @property
    def _is_sun_up(self) -> bool:
        """Return True if the sun is up at the location."""
        current_time = time.time()
        return all(
            [
                current_time > self._data.get("current", {}).get("sunrise"),
                current_time < self._data.get("current", {}).get("sunset"),
            ]
        )


class GoogleNestWeatherForecast(object):

    def __init__(self, data) -> None:
        self._data = data

    @property
    def daily(self) -> list[Forecast]:
        forecast = []
        for item in self._data.get("forecast", {}).get("daily", []):
            forecast.append(
                {
                    ATTR_FORECAST_CONDITION: CONDITION_MAP.get(item["condition"], item["condition"]),
                    ATTR_FORECAST_NATIVE_TEMP: item["temp_high_c"],
                    ATTR_FORECAST_NATIVE_TEMP_LOW: item["temp_low_c"],
                    ATTR_FORECAST_TIME: f"{datetime.fromtimestamp(item['date']).isoformat()}Z",
                }
            )
            if item["condition"] not in CONDITION_MAP.keys():
                _LOGGER.debug(f'Found unmapped weather condition - {item["condition"]}')
        return forecast

    @property
    def hourly(self) -> list[Forecast]:
        forecast = []
        for item in self._data.get("forecast", {}).get("hourly", []):
            forecast.append(
                {
                    ATTR_FORECAST_NATIVE_TEMP: item["temp_c"],
                    ATTR_FORECAST_HUMIDITY: item["humidity"],
                    ATTR_FORECAST_TIME: f"{datetime.fromtimestamp(item['time']).isoformat()}Z",
                }
            )
        return forecast
