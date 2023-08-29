"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bucket import Bucket


@dataclass
class SafetyBucketValue:
    """Safety values."""

    audio_self_test_enabled: bool
    audio_self_test_end_utc_offset_secs: int
    audio_self_test_force_interval_secs: int
    audio_self_test_in_progress: bool
    audio_self_test_notify: bool
    audio_self_test_participants: list[str]
    audio_self_test_repeat_interval_secs: int
    audio_self_test_request_utc_secs: int
    audio_self_test_skip_utc_secs: int
    audio_self_test_start_utc_offset_secs: int
    co_history_duration_secs: int
    fd_in_progress: bool
    last_audio_self_test_end_utc_secs: int
    last_audio_self_test_start_utc_secs: int
    last_fd_user_closed_doors: bool
    last_fd_user_found_phone: bool
    last_fd_user_identified_two_ways: bool
    last_fd_user_met_at_meeting_place: bool
    last_fd_user_stayed_low_while_exiting: bool
    last_fd_user_tested_doors_before_entering: bool
    last_fd_user_took_headcount: bool
    last_manual_self_test_cancelled: bool
    last_manual_self_test_end_utc_secs: int
    last_manual_self_test_start_utc_secs: int
    last_manual_self_test_success_utc_secs: int
    manual_self_test_in_progress: bool
    smoke_history_duration_secs: int


@dataclass
class SafetyBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: SafetyBucketValue = field(default_factory=SafetyBucketValue)


@dataclass
class StructureBucketValue:
    """Structure values."""

    address_lines: list[str]
    aux_primary_fabric_id: str
    away: bool
    away_setter: int
    away_timestamp: int
    campaign_id:str
    city: str
    clutches: list
    country_code: str
    creation_time: int
    demand_charge_enabled: bool
    devices: list[str]
    dr_reminder_enabled: bool
    enable_goose: bool
    entitlements: dict
    eta_last_active_unique_id: str
    eta_preconditioning_active: bool
    eta_unique_id: str
    fabric_ids: list[str]
    geofence_enhanced_autoaway: dict[str, bool]
    goose_sensor_events_enabled: bool
    house_type: str
    hvac_safety_shutoff_enabled: bool
    hvac_smoke_safety_shutoff_enabled: bool
    ifj_primary_fabric_id: str
    last_action: str
    last_action_by: str
    latitude: float
    location: str
    longitude: float
    manual_away_timestamp: int
    manual_eco_all: bool
    measurement_scale: str
    members: list[dict[str, Any]]
    name: str
    num_thermostats: str
    phone_hush_enable: bool
    postal_code: str
    rcs_sensor_swarm: list[str]
    renovation_date: str
    state: str
    structure_area: float
    swarm: list[str]
    time_zone: str
    topaz_away: bool
    topaz_enhanced_auto_away_enabled: bool
    topaz_hush_key: str
    tou_enabled: bool
    tou_speedbump_count_remaining: int
    touched_by: dict[str, Any]
    user: str
    vacation_mode: bool


@dataclass
class StructureBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: StructureBucketValue = field(default_factory=StructureBucketValue)
