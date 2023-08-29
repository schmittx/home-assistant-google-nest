"""Constants used by Nest."""
from __future__ import annotations

from .models import NestEnvironment

# App launch API endpoint
APP_LAUNCH_URL_FORMAT: str = "{host}/api/0.1/user/{user_id}/app_launch"

KNOWN_BUCKET_TYPES: list[str] = [
  "buckets",
  "delayed_topaz",
  "demand_response",
  "device",
  "device_alert_dialog",
  "geofence_info",
  "kryptonite",
  "link",
  "message",
  "message_center",
  "metadata",
  "occupancy",
  "quartz",
  "safety",
  "rcs_settings",
  "safety_summary",
  "schedule",
  "shared",
  "structure",
  "structure_history",
  "structure_metadata",
  "topaz",
  "topaz_resource",
  "track",
  "trip",
  "tuneups",
  "user",
  "user_alert_dialog",
  "user_settings",
  "where",
  "widget_track",
]

KNOWN_BUCKET_VERSIONS: list = []

NEST_AUTH_URL_JWT: str = "https://nestauthproxyservice-pa.googleapis.com/v1/issue_jwt"

NEST_ENVIRONMENTS: dict[str, NestEnvironment] = {
    "production": NestEnvironment(
        name="Google Account",
        client_id="733249279899-1gpkq9duqmdp55a7e5lft1pr2smumdla.apps.googleusercontent.com",  # Nest iOS application
        host="https://home.nest.com",
    ),
    "fieldtest": NestEnvironment(
        name="Google Account (Field Test)",
        client_id="384529615266-57v6vaptkmhm64n9hn5dcmkr4at14p8j.apps.googleusercontent.com",  # Test Flight Beta Nest iOS application
        host="https://home.ft.nest.com",
    ),
}

SAVE_RESPONSE_LOCATION: str = "/config/custom_components/google_nest/api/responses"

SENSOR_SCHEDULE_INTERVALS: dict[str, int] = {
    "morning": 25201,
    "midday": 39601,
    "evening": 57601,
    "night": 75601,
}

# URL for refresh token generation
TOKEN_URL: str = "https://oauth2.googleapis.com/token"

USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"

DEFAULT_NEST_ENVIRONMENT: NestEnvironment = NEST_ENVIRONMENTS["production"]

NEST_REQUEST: dict[str, list] = {
    "known_bucket_types": KNOWN_BUCKET_TYPES,
    "known_bucket_versions": KNOWN_BUCKET_VERSIONS,
}

