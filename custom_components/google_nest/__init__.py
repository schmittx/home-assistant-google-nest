"""The Google Nest integration."""
from __future__ import annotations

from aiohttp import ClientConnectorError, ClientError, ServerDisconnectedError
import async_timeout
import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_ACCOUNT_TYPE,
    CONF_COOKIES,
    CONF_ISSUE_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LOGGER,
)
from .api.client import NestClient
from .api.const import NEST_ENVIRONMENTS
from .api.exceptions import (
    BadCredentialsException,
    NestServiceException,
    NotAuthenticatedException,
    NestException,
)
from .api.models import (
    Bucket,
    DeviceBucket,
    KryptoniteBucket,
    LinkBucket,
    QuartzBucket,
    RcsSettingsBucket,
    SafetyBucket,
    SharedBucket,
    StructureBucket,
    TopazBucket,
    TrackBucket,
    Camera,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.HUMIDIFIER,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.WEATHER,
]

@dataclass
class HomeAssistantGoogleNestData:
    """Google Nest data stored in the Home Assistant data object."""

    client: NestClient
    structures: dict[str, str]
    thermostats: dict[str, str]
    thermostat_device_info: dict[str, dict]
    sensors: dict[str, str]
    areas: dict[str, str]
    swarms: dict[str, str]
    time_zones: dict[str, str]
    devices: dict[str, Bucket]
    coordinators: dict[str, DataUpdateCoordinator]
    undo_update_listener: CALLBACK_TYPE


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old Config entries."""
    LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        entry_data = {**config_entry.data}
        entry_data[CONF_ACCOUNT_TYPE] = "production"

        config_entry.data = {**entry_data}
        config_entry.version = 2

    LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Nest from a config entry."""
    conf_account_type = config_entry.data[CONF_ACCOUNT_TYPE]
    conf_cookies = config_entry.data.get(CONF_COOKIES)
    conf_issue_token = config_entry.data.get(CONF_ISSUE_TOKEN)
    conf_refresh_token = config_entry.data.get(CONF_REFRESH_TOKEN)

    conf_save_responses = config_entry.options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
    conf_scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    conf_timeout = config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    session = async_get_clientsession(hass)
    client = NestClient(
        session=session,
        environment=NEST_ENVIRONMENTS[conf_account_type],
        save_response_enabled=conf_save_responses,
    )

    try:
        if conf_issue_token and conf_cookies:
            auth = await client.get_access_token_from_cookies(conf_issue_token, conf_cookies)
        elif conf_refresh_token:
            auth = await client.get_access_token_from_refresh_token(conf_refresh_token)
        else:
            raise Exception(
                "No issue_token and cookies, or refresh_token. Please provide issue_token and cookies, or refresh_token."
            )
        nest = await client.authenticate(auth.access_token)
    except (TimeoutError, ClientError) as exception:
        raise ConfigEntryNotReady from exception
    except BadCredentialsException as exception:
        raise ConfigEntryAuthFailed from exception
    except Exception as exception:  # pylint: disable=broad-except
        LOGGER.exception(exception)
        raise ConfigEntryNotReady from exception

    data = await client.get_first_data(nest.access_token, nest.userid)

    structures: dict[str, str] = {} #id: name
    thermostats: dict[str, str] = {} #device_id: where_id
    thermostat_device_info: dict[str, dict] = {}
    sensors: dict[str, str] = {} #kryptonite.device_id: where_id
    areas: dict[str, str] = {}
    swarms: dict[str, str] = {} #child id: parent id
    time_zones: dict[str, str] = {} #id: time zone
    devices: list[Bucket] = []
    coordinators: dict[str, DataUpdateCoordinator] = {}

    def update_camera_data(id, activity_zones):
        async def async_update_data():
            """Fetch data from API endpoint.

            This is the place to pre-process the data to lookup tables
            so entities can quickly look up their data.
            """
            try:
                cache = hass.data[DOMAIN][config_entry.entry_id].coordinators[id].data
            except KeyError:
                _LOGGER.debug(f"No cache data found for {id}")
                cache = None
            data = {}
            try:
                async with async_timeout.timeout(conf_timeout):
                    data["alerts"] = await client.get_camera_alerts(uuid=id, alert_interval=300)
                    data["properties"] = await client.get_camera_properties(uuid=id)
                if conf_save_responses:
                    client.save_response(data, f"camera_{id}")
                return Camera(client, data, id, activity_zones)
            except NestException as exception:
                message = f"Error communicating with API, exception: {exception}"
                if cache:
                    _LOGGER.warning(f"{message}, using cached data")
                    return cache
                raise UpdateFailed(message)

        return async_update_data

    for bucket in data["updated_buckets"]:
        key = bucket["object_key"]
        id = key.split(".")[1]

        # Cameras
        if key.startswith("quartz."):
            devices.append(QuartzBucket(**bucket))
            activity_zones = bucket["value"].get("activity_zones", [])
            coordinators[id] = DataUpdateCoordinator(
                hass=hass,
                logger=_LOGGER,
                name=f"{DOMAIN}_{id}",
                update_method=update_camera_data(id, activity_zones),
                update_interval=timedelta(seconds=conf_scan_interval),
            )
            await coordinators[id].async_config_entry_first_refresh()

        # Protects
        if key.startswith("topaz."):
            devices.append(TopazBucket(**bucket))

        # Structures
        if key.startswith("safety."):
            devices.append(SafetyBucket(**bucket))

        if key.startswith("structure."):
            structure = StructureBucket(**bucket)
            devices.append(structure)
            structures[id] = structure.value["name"]
            time_zones[id] = structure.value["time_zone"]

        # Thermostats
        if key.startswith("device."):
            device = DeviceBucket(**bucket)
            devices.append(device)
            thermostats[id] = device.value["where_id"]
            thermostat_device_info[id] = {
                "model_version": device.value["model_version"],
                "current_version": device.value["current_version"],
            }

        if key.startswith("link."):
            link = LinkBucket(**bucket)
            devices.append(link)
            swarms[id] = link.value["structure"].split(".")[1]

        if key.startswith("rcs_settings."):
            rcs_settings = RcsSettingsBucket(**bucket)
            devices.append(rcs_settings)
            for sensor in rcs_settings.value["associated_rcs_sensors"]:
                swarms[sensor.split(".")[1]] = id

        if key.startswith("shared."):
            devices.append(SharedBucket(**bucket))

        if key.startswith("track."):
            devices.append(TrackBucket(**bucket))

        # Temperature Sensors
        if key.startswith("kryptonite."):
            kryptonite = KryptoniteBucket(**bucket)
            devices.append(kryptonite)
            sensors[key] = kryptonite.value["where_id"]

        # Areas
        if key.startswith("where."):
            bucket_value = Bucket(**bucket).value
            for area in bucket_value["wheres"]:
                areas[area["where_id"]] = area["name"]


    devices: dict[str, Bucket] = {b.object_key: b for b in devices}

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = HomeAssistantGoogleNestData(
        client=client,
        structures=structures,
        thermostats=thermostats,
        thermostat_device_info=thermostat_device_info,
        sensors=sensors,
        areas=areas,
        swarms=swarms,
        time_zones=time_zones,
        devices=devices,
        coordinators=coordinators,
        undo_update_listener=config_entry.add_update_listener(async_update_listener),
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Subscribe for real-time updates
    # TODO cancel when closing HA / unloading entry
    _register_subscribe_task(hass, config_entry, data)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
    """Remove a config entry from a device."""
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry=config_entry,
        platforms=PLATFORMS,
    ):
        hass.data[DOMAIN][config_entry.entry_id].undo_update_listener()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


def _register_subscribe_task(hass: HomeAssistant, config_entry: ConfigEntry, data: Any):
    return asyncio.create_task(_async_subscribe_for_data(hass, config_entry, data))


async def _async_subscribe_for_data(hass: HomeAssistant, config_entry: ConfigEntry, data: Any):
    """Subscribe for new data."""
    entry_data: HomeAssistantGoogleNestData = hass.data[DOMAIN][config_entry.entry_id]

    try:
        # TODO move refresh token logic to client
        if (
            not entry_data.client.nest_session
            or entry_data.client.nest_session.is_expired()
        ):
            LOGGER.debug("Subscriber: authenticate for new Nest session")

        if not entry_data.client.auth or entry_data.client.auth.is_expired():
            LOGGER.debug("Subscriber: retrieving new Google access token")
#            await entry_data.client.get_access_token()
#            await entry_data.client.authenticate(entry_data.client.auth.access_token)
            auth = await entry_data.client.get_access_token()
            entry_data.client.nest_session = await entry_data.client.authenticate(auth)


        # Subscribe to Google Nest subscribe endpoint
        result = await entry_data.client.subscribe_for_data(
            entry_data.client.nest_session.access_token,
            entry_data.client.nest_session.userid,
            data["service_urls"]["urls"]["transport_url"],
            data["updated_buckets"],
        )

        for bucket in result["objects"]:
            key = bucket["object_key"]

            # Cameras
            if key.startswith("quartz."):
                quartz = QuartzBucket(**bucket)
                entry_data.devices[key] = quartz
#                await entry_data.coordinators[key.split(".")[1]].async_refresh()

                async_dispatcher_send(hass, key, quartz)

            # Protects
            if key.startswith("topaz."):
                topaz = TopazBucket(**bucket)
                entry_data.devices[key] = topaz

                async_dispatcher_send(hass, key, topaz)

            # Structures
            if key.startswith("safety."):
                safety = SafetyBucket(**bucket)
                entry_data.devices[key] = safety

                async_dispatcher_send(hass, key, safety)

            if key.startswith("structure."):
                structure = StructureBucket(**bucket)
                entry_data.devices[key] = structure
                entry_data.structures[key.split(".")[1]] = structure.value["name"]
                entry_data.time_zones[key.split(".")[1]] = structure.value["time_zone"]

                async_dispatcher_send(hass, key, structure)

            # Thermostats
            if key.startswith("device."):
                device = DeviceBucket(**bucket)
                entry_data.devices[key] = device
                entry_data.thermostats[key.split(".")[1]] = device.value["where_id"]
                entry_data.thermostat_device_info[key.split(".")[1]] = {
                    "model_version": device.value["model_version"],
                    "current_version": device.value["current_version"],
                }

                async_dispatcher_send(hass, key, device)

            if key.startswith("link."):
                link = LinkBucket(**bucket)
                entry_data.devices[key] = link
                entry_data.swarms[key.split(".")[1]] = link.value["structure"].split(".")[1]

                async_dispatcher_send(hass, key, link)

            if key.startswith("rcs_settings."):
                rcs_settings = RcsSettingsBucket(**bucket)
                entry_data.devices[key] = rcs_settings
                for sensor in rcs_settings.value["associated_rcs_sensors"]:
                    entry_data.swarms[sensor.split(".")[1]] = key.split(".")[1]

                async_dispatcher_send(hass, key, rcs_settings)

            if key.startswith("shared."):
                shared = SharedBucket(**bucket)
                entry_data.devices[key] = shared

                async_dispatcher_send(hass, key, shared)

            if key.startswith("track."):
                track = TrackBucket(**bucket)
                entry_data.devices[key] = track

                async_dispatcher_send(hass, key, track)

            # Temperature Sensors
            if key.startswith("kryptonite."):
                kryptonite = KryptoniteBucket(**bucket)
                entry_data.devices[key] = kryptonite
                entry_data.sensors[key] = kryptonite.value["where_id"]

                # TODO investigate if we want to use dispatcher, or get data from entry data in sensors
                async_dispatcher_send(hass, key, kryptonite)

            # Areas
            if key.startswith("where."):
                bucket_value = Bucket(**bucket).value
                for area in bucket_value["wheres"]:
                    entry_data.areas[area["where_id"]] = area["name"]

        # Update buckets with new data, to only receive new updates
        buckets = {d["object_key"]: d for d in result["objects"]}
        objects = [
            dict(d, **buckets.get(d["object_key"], {})) for d in data["updated_buckets"]
        ]

        data["updated_buckets"] = objects
        _register_subscribe_task(hass, config_entry, data)

    except ServerDisconnectedError:
        LOGGER.debug("Subscriber: server disconnected.")
        _register_subscribe_task(hass, config_entry, data)

    except asyncio.exceptions.TimeoutError:
        LOGGER.debug("Subscriber: session timed out.")
        _register_subscribe_task(hass, config_entry, data)

    except ClientConnectorError:
        LOGGER.debug("Subscriber: cannot connect to host.")
        _register_subscribe_task(hass, config_entry, data)

    except NotAuthenticatedException:
        LOGGER.debug("Subscriber: 401 exception.")
        # Renewing access token
        await entry_data.client.get_access_token()
        await entry_data.client.authenticate(entry_data.client.auth.access_token)
        _register_subscribe_task(hass, config_entry, data)

    except NestServiceException:
        LOGGER.debug("Subscriber: Nest Service error. Updates paused for 2 minutes.")

        await asyncio.sleep(60 * 2)
        _register_subscribe_task(hass, config_entry, data)

    except NestException:
        LOGGER.exception(
            "Unknown Nest exception. Please create an issue on GitHub with your logfile. Updates paused for 1 minute."
        )

        # Wait a minute before retrying
        await asyncio.sleep(60)
        _register_subscribe_task(hass, config_entry, data)

    except Exception:  # pylint: disable=broad-except
        # Wait 5 minutes before retrying
        await asyncio.sleep(60 * 5)
        _register_subscribe_task(hass, config_entry, data)

        LOGGER.exception(
            "Unknown exception. Please create an issue on GitHub with your logfile. Updates paused for 5 minutes."
        )
