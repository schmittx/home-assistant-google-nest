"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bucket import Bucket


@dataclass
class QuartzBucketValue:
    """Camera values."""

    activation_time: int
    activity_zones: list[dict[str, Any]]
    audio_input_enabled: bool
    camera_type: int
    capabilities: list[str]
    cvr_enrolled: str
    description: str
    direct_nexustalk_host: str
    download_host: str
    fabric_id: str
    google_assistant: dict[str, bool]
    ip_address: str
    last_connect_time: int
    last_cuepoint: dict[str, Any]
    last_disconnect_reason: str
    last_disconnect_time: int
    live_stream_host: str
    mac_address: str
    model: str
    nexus_api_http_server_url: str
    person_event: dict[str, int]
    preview_streaming_enabled: bool
    public_share_enabled: bool
    recorded_stream_host: str
    serial_number: str
    snapshot_url: dict[str, str]
    software_version: str
    streaming_enabled_by_wwn: dict[str, Any]
    streaming_state: str
    structure_id: str
    weave_device_id: str
    websocket_nexustalk_host: str
    where_id: str
    wwn_stream_host: str


@dataclass
class QuartzBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: QuartzBucketValue = field(default_factory=QuartzBucketValue)


class Camera(object):

    def __init__(self, client, data, uuid, activity_zones) -> None:
        self.client = client
        self.data = data
        self.uuid = uuid
        self.activity_zones = activity_zones

    @property
    def _alerts(self) -> dict:
        return self.data.get("alerts", {})

    @property
    def _properties(self) -> dict:
        return self.data.get("properties", {})

    @property
    def items(self) -> list:
        return self._properties.get("items", [])

    @property
    def item(self) -> dict:
        if self.items:
            return self.items[0]
        return {}

    @property
    def capabilities(self) -> list:
        return self.item.get("capabilities", [])

    @property
    def properties(self) -> dict:
        return self.item.get("properties", {})

    @property
    def is_connected(self) -> bool | None:
        return self.item.get("is_connected")

    @property
    def alerts(self) -> list[Alert]:
        return [Alert(alert) for alert in self._alerts]

    @property
    def zones(self) -> list[Zone]:
        return [Zone(self.alerts, activity_zone) for activity_zone in self.activity_zones]

    @property
    def button_pressed(self) -> bool:
        return any([alert.button_pressed for alert in self.alerts])

    @property
    def dog_barking_detected(self) -> bool:
        return any([alert.dog_barking_detected for alert in self.alerts])

    @property
    def face_detected(self) -> bool:
        return any([alert.face_detected for alert in self.alerts])

    @property
    def motion_detected(self) -> bool:
        return any([alert.motion_detected for alert in self.alerts if not alert.zone_ids or 0 in alert.zone_ids])

    @property
    def package_delivered(self) -> bool:
        return any([alert.package_delivered for alert in self.alerts if not alert.zone_ids or 0 in alert.zone_ids])

    @property
    def package_retrieved(self) -> bool:
        return any([alert.package_retrieved for alert in self.alerts if not alert.zone_ids or 0 in alert.zone_ids])

    @property
    def person_detected(self) -> bool:
        return any([alert.person_detected for alert in self.alerts if not alert.zone_ids or 0 in alert.zone_ids])

    @property
    def person_talking_detected(self) -> bool:
        return any([alert.person_talking_detected for alert in self.alerts])

    @property
    def sound_detected(self) -> bool:
        return any([alert.sound_detected for alert in self.alerts])

    @property
    def face_names(self) -> list[str]:
        face_names = []
        for alert in self.alerts:
            if alert.face_detected and alert.face_name not in face_names:
                face_names.append(alert.face_name)
        return face_names


class Alert(object):

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def camera_uuid(self) -> str | None:
        return self.data.get("camera_uuid")

    @property
    def end_time(self) -> int | None:
        return self.data.get("end_time")

    @property
    def face_category(self) -> str | None:
        return self.data.get("face_category")

    @property
    def face_id(self) -> str | None:
        return self.data.get("face_id")

    @property
    def face_name(self) -> str | None:
        return self.data.get("face_name")

    @property
    def id(self) -> str | None:
        return self.data.get("id")

    @property
    def importance(self) -> int | None:
        return self.data.get("importance")

    @property
    def in_progress(self) -> bool | None:
        return self.data.get("in_progress")

    @property
    def is_important(self) -> bool | None:
        return self.data.get("is_important")

    @property
    def playback_time(self) -> int | None:
        return self.data.get("playback_time")

    @property
    def start_time(self) -> int | None:
        return self.data.get("start_time")

    @property
    def types(self) -> list[str]:
        return self.data.get("types", [])

    @property
    def zone_ids(self) -> list[int]:
        return self.data.get("zone_ids", [])

    @property
    def button_pressed(self) -> bool:
        return bool("doorbell" in self.types)

    @property
    def dog_barking_detected(self) -> bool:
        return bool("dog-barking" in self.types)

    @property
    def face_detected(self) -> bool:
        return bool("face" in self.types)

    @property
    def motion_detected(self) -> bool:
        return bool("motion" in self.types)

    @property
    def package_delivered(self) -> bool:
        return bool("package-delivered" in self.types)

    @property
    def package_retrieved(self) -> bool:
        return bool("package-retrieved" in self.types)

    @property
    def person_detected(self) -> bool:
        return bool("person" in self.types)

    @property
    def person_talking_detected(self) -> bool:
        return bool("person-talking" in self.types)

    @property
    def sound_detected(self) -> bool:
        return bool("sound" in self.types)


class Zone(object):

    def __init__(self, alerts, activity_zone) -> None:
        self.alerts = alerts
        self.activity_zone = activity_zone

    @property
    def id(self) -> int | None:
        return self.activity_zone.get("id")

    @property
    def name(self) -> str | None:
        return self.activity_zone.get("name")

    @property
    def motion_detected(self) -> bool:
        for alert in self.alerts:
            if all(
                [
                    alert.motion_detected,
                    self.id in alert.zone_ids,
                ]
            ):
                return True
        return False

    @property
    def person_detected(self) -> bool:
        for alert in self.alerts:
            if all(
                [
                    alert.person_detected,
                    self.id in alert.zone_ids,
                ]
            ):
                return True
        return False

    @property
    def package_delivered(self) -> bool:
        for alert in self.alerts:
            if all(
                [
                    alert.package_delivered,
                    self.id in alert.zone_ids,
                ]
            ):
                return True
        return False

    @property
    def package_retrieved(self) -> bool:
        for alert in self.alerts:
            if all(
                [
                    alert.package_retrieved,
                    self.id in alert.zone_ids,
                ]
            ):
                return True
        return False
