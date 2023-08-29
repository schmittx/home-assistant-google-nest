"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field

from .bucket import Bucket


@dataclass
class TopazBucketValue:
    """Protect values."""

    auto_away: bool
    auto_away_decision_time_secs: int
    battery_health_state: int
    battery_level: int
    buzzer_test_results: int
    capability_level: float
    certification_body: int
    co_blame_duration: int
    co_blame_threshold: int
    co_previous_peak: int
    co_sequence_number: int
    co_status: int
    component_als_test_passed: bool
    component_buzzer_test_passed: bool
    component_co_test_passed: bool
    component_heat_test_passed: bool
    component_hum_test_passed: bool
    component_led_test_passed: bool
    component_pir_test_passed: bool
    component_smoke_test_passed: bool
    component_speaker_test_passed: bool
    component_temp_test_passed: bool
    component_us_test_passed: bool
    component_wifi_test_passed: bool
    creation_time: int
    device_born_on_date_utc_secs: int
    device_external_color: str
    device_locale: str
    fabric_id: str
    gesture_hush_enable: bool
    heads_up_enable: bool
    heat_status: int
    home_alarm_link_capable: bool
    home_alarm_link_connected: bool
    home_alarm_link_type: int
    home_away_input: bool
    hushed_state: bool
    installed_locale: str
    is_rcs_capable: bool
    is_rcs_used: bool
    kl_software_version: str
    last_audio_self_test_end_utc_secs: int
    last_audio_self_test_start_utc_secs: int
    latest_manual_test_cancelled: bool
    latest_manual_test_end_utc_secs: int
    latest_manual_test_start_utc_secs: int
    line_power_present: bool
    model: str
    night_light_brightness: int
    night_light_continuous: bool
    night_light_enable: bool
    ntp_green_led_brightness: int
    ntp_green_led_enable: bool
    product_id: int
    removed_from_base: bool
    replace_by_date_utc_secs: int
    resource_id: str
    serial_number: str
    smoke_sequence_number: int
    smoke_status: int
    software_version: str
    speaker_test_results: int
    spoken_where_id: str
    steam_detection_enable: bool
    structure_id: str
    thread_ip_address: list[str]
    thread_mac_address: str
    where_id: str
    wifi_ip_address: str
    wifi_mac_address: str
    wifi_regulatory_domain: str
    wired_led_enable: bool
    wired_or_battery: int


@dataclass
class TopazBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: TopazBucketValue = field(default_factory=TopazBucketValue)
