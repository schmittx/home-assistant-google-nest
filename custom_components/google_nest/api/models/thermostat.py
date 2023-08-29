"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bucket import Bucket


@dataclass
class DeviceBucketValue:
    """Device values."""

    alt_heat_delivery: str
    alt_heat_source: str
    alt_heat_x2_delivery: str
    alt_heat_x2_source: str
    auto_away_enable: bool
    auto_away_reset: bool
    auto_dehum_enabled: bool
    auto_dehum_state: bool
    aux_heat_delivery: str
    aux_heat_source: str
    aux_lockout_leaf: float
    available_locales: str
    away_temperature_high: float
    away_temperature_high_adjusted: float
    away_temperature_high_enabled: bool
    away_temperature_low: float
    away_temperature_low_adjusted: float
    away_temperature_low_enabled: bool
    backplate_bsl_info: str
    backplate_bsl_version: str
    backplate_model: str
    backplate_mono_info: str
    backplate_mono_version: str
    backplate_serial_number: str
    backplate_temperature: float
    battery_level: float
    capability_level: float
    click_sound: str
    compressor_lockout_leaf: float
    cooling_delivery: str
    cooling_source: str
    cooling_x2_delivery: str
    cooling_x2_source: str
    cooling_x3_delivery: str
    cooling_x3_source: str
    country_code: str
    creation_time: int
    current_humidity: int
    current_schedule_mode: str
    current_version: str
    dehumidifier_orientation_selected: str
    dehumidifier_state: bool
    dehumidifier_type: str
    device_locale: str
    dual_fuel_breakpoint: float
    dual_fuel_breakpoint_override: str
    eco: dict[str, Any]
    eco_onboarding_needed: bool
    emer_heat_delivery: str
    emer_heat_enable: bool
    emer_heat_source: str
    error_code: str
    fan_capabilities: str
    fan_control_state: bool
    fan_cooling_enabled: bool
    fan_cooling_readiness: str
    fan_cooling_state: bool
    fan_current_speed: str
    fan_duty_cycle: int
    fan_duty_end_time: int
    fan_duty_start_time: int
    fan_heat_cool_speed: str
    fan_mode: str
    fan_schedule_speed: str
    fan_timer_duration: int
    fan_timer_speed: str
    fan_timer_timeout: int
    farsight_screen: str
    filter_changed_date: int
    filter_changed_set_date: int
    filter_reminder_enabled: bool
    filter_reminder_level: int
    filter_replacement_needed: bool
    filter_replacement_threshold_sec: int
    filter_runtime_sec: int
    forced_air: bool
    gear_threshold_high: float
    gear_threshold_low: float
    has_air_filter: bool
    has_alt_heat: bool
    has_aux_heat: bool
    has_dehumidifier: bool
    has_dual_fuel: bool
    has_emer_heat: bool
    has_fan: bool
    has_fossil_fuel: bool
    has_heat_pump: bool
    has_hot_water_control: bool
    has_hot_water_temperature: bool
    has_humidifier: bool
    has_x2_alt_heat: bool
    has_x2_cool: bool
    has_x2_heat: bool
    has_x3_cool: bool
    has_x3_heat: bool
    heat_link_connection: int
    heat_pump_aux_threshold: float
    heat_pump_aux_threshold_enabled: bool
    heat_pump_comp_threshold: float
    heat_pump_comp_threshold_enabled: bool
    heat_x2_delivery: str
    heat_x2_source: str
    heat_x3_delivery: str
    heat_x3_source: str
    heater_delivery: str
    heater_source: str
    heatpump_ready: bool
    heatpump_savings: str
    heatpump_setback_active: bool
    home_away_input: bool
    hot_water_active: bool
    hot_water_away_active: bool
    hot_water_away_enabled: bool
    hot_water_boiling_state: bool
    humidifier_fan_activation: bool
    humidifier_state: bool
    humidifier_type: str
    humidity_control_lockout_enabled: bool
    humidity_control_lockout_end_time: int
    humidity_control_lockout_start_time: int
    hvac_pins: str
    hvac_safety_shutoff_active: bool
    hvac_smoke_safety_shutoff_active: bool
    hvac_staging_ignore: bool
    hvac_wires: str
    is_furnace_shutdown: bool
    kryptonite_range_test_timestamp: int
    last_software_update_utc_secs: int
    leaf: bool
    leaf_away_high: float
    leaf_away_low: float
    leaf_schedule_delta: float
    leaf_threshold_cool: float
    leaf_threshold_heat: float
    learning_mode: bool
    local_ip: str
    logging_priority: str
    lower_safety_temp: float
    lower_safety_temp_enabled: bool
    mac_address: str
    maint_band_lower: float
    maint_band_upper: float
    max_nighttime_preconditioning_seconds: int
    model_version: str
    nlclient_state: str
    ob_orientation: str
    ob_persistence: bool
    oob_interview_completed: bool
    oob_startup_completed: bool
    oob_summary_completed: bool
    oob_temp_completed: bool
    oob_test_completed: bool
    oob_where_completed: bool
    oob_wifi_completed: bool
    oob_wires_completed: bool
    pin_c_description: str
    pin_g_description: str
    pin_ob_description: str
    pin_rc_description: str
    pin_rh_description: str
    pin_star_description: str
    pin_w1_description: str
    pin_w2aux_description: str
    pin_y1_description: str
    pin_y2_description: str
    postal_code: str
    preconditioning_active: bool
    preconditioning_enabled: bool
    preconditioning_ready: bool
    pro_id: str
    radiant_control_enabled: bool
    rcs_capable: bool
    rssi: float
    safety_state: str
    safety_state_time: int
    safety_temp_activating_hvac: bool
    schedule_learning_reset: bool
    schedules: list[Any]
    serial_number: str
    should_wake_on_approach: bool
    smoke_shutoff_supported: bool
    star_type: str
    sunlight_correction_active: bool
    sunlight_correction_enabled: bool
    sunlight_correction_ready: bool
    target_humidity: float
    target_humidity_enabled: bool
    temperature_lock: bool
    temperature_lock_high_temp: float
    temperature_lock_low_temp: float
    temperature_lock_pin_hash: str
    temperature_scale: str
    time_to_target: int
    time_to_target_training: str
    touched_by: dict[Any]
    upper_safety_temp: float
    upper_safety_temp_enabled: bool
    weave_device_id: str
    where_id: str
    wiring_error: str
    wiring_error_timestamp: int
    y2_type: str


@dataclass
class DeviceBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: DeviceBucketValue = field(default_factory=DeviceBucketValue)


@dataclass
class LinkBucketValue:
    """Link values."""

    structure: str


@dataclass
class LinkBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: LinkBucketValue = field(default_factory=LinkBucketValue)


@dataclass
class RcsSettingsBucketValue:
    """RCS Settings values."""

    active_rcs_sensors: list[Any]
    associated_rcs_sensors: list[str]
    multiroom_active: bool
    rcs_control_setting: str
    sensor_insights: dict[str, list[dict[str, Any]]]
    sensor_schedule: dict[str, list[dict[str, Any]]]
    thermostat_alert: str


@dataclass
class RcsSettingsBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: RcsSettingsBucketValue = field(default_factory=RcsSettingsBucketValue)


@dataclass
class SharedBucketValue:
    """Shared values."""

    auto_away: int
    auto_away_learning: str
    can_cool: bool
    can_heat: bool
    compressor_lockout_enabled: bool
    compressor_lockout_timeout: int
    current_temperature: float
    hvac_ac_state: bool
    hvac_alt_heat_state: bool
    hvac_alt_heat_x2_state: bool
    hvac_aux_heater_state: bool
    hvac_cool_x2_state: bool
    hvac_cool_x3_state: bool
    hvac_emer_heat_state: bool
    hvac_fan_state: bool
    hvac_heat_x2_state: bool
    hvac_heat_x3_state: bool
    hvac_heater_state: bool
    name: str
    target_change_pending: bool
    target_temperature: float
    target_temperature_high: float
    target_temperature_low: float
    target_temperature_type: str
    touched_by: dict[Any]


@dataclass
class SharedBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: SharedBucketValue = field(default_factory=SharedBucketValue)


@dataclass
class TrackBucketValue:
    """Track values."""

    last_connection: int
    last_ip: str
    online: bool


@dataclass
class TrackBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: TrackBucketValue = field(default_factory=TrackBucketValue)
