"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any

from .bucket import Bucket
from .camera import QuartzBucket, Camera, Zone
from .protect import TopazBucket
from .structure import SafetyBucket, StructureBucket
from .temperature_sensor import KryptoniteBucket
from .thermostat import DeviceBucket, LinkBucket, RcsSettingsBucket, SharedBucket, TrackBucket


@dataclass
class NestLimits:
    """Nest Limits."""

    thermostats_per_structure: int
    structures: int
    smoke_detectors_per_structure: int
    smoke_detectors: int
    thermostats: int


@dataclass
class NestUrls:
    """Nest Urls."""

    rubyapi_url: str
    czfe_url: str
    log_upload_url: str
    transport_url: str
    weather_url: str
    support_url: str
    direct_transport_url: str


@dataclass
class NestResponse:
    """Class that reflects a Nest API response."""

    access_token: float
    email: str
    expires_in: str
    userid: str
    is_superuser: bool
    language: str
    weave: dict[str, str]
    user: str
    is_staff: bool
    error: dict | None = None
    urls: NestUrls = field(default_factory=NestUrls)
    limits: NestLimits = field(default_factory=NestLimits)

    _2fa_state: str = None
    _2fa_enabled: bool = None
    _2fa_state_changed: str = None

    def is_expired(self):
        """Check if session is expired."""
        # Tue, 01-Mar-2022 23:15:55 GMT
        expiry_date = datetime.datetime.strptime(
            self.expires_in, "%a, %d-%b-%Y %H:%M:%S %Z"
        )

        if expiry_date <= datetime.datetime.now():
            return True

        return False


@dataclass
class GoogleAuthResponse:
    """Class that reflects a Google Auth response."""

    access_token: str
    expires_in: int
    scope: str
    token_type: str
    id_token: str
    expiry_date: datetime.datetime = field(init=False)

    def __post_init__(self):
        """Set the expiry date during post init."""
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(
            seconds=self.expires_in
        )

    def is_expired(self):
        """Check if access token is expired."""
        if self.expiry_date <= datetime.datetime.now():
            return True

        return False


@dataclass
class GoogleAuthResponseForCookies(GoogleAuthResponse):
    """Class that reflects a Google Auth response for cookies."""

    login_hint: str
    session_state: dict[str, dict[str, str]] = field(default_factory=dict)


# TODO rewrite to snake_case
@dataclass
class NestAuthClaims:
    """TODO."""

    subject: Any
    expirationTime: str
    policyId: str
    structureConstraint: str
    subject: Any | None = None
    expirationTime: str | None = None
    policyId: str | None = None
    structureConstraint: str | None = None


@dataclass
class NestAuthResponse:
    """TODO."""

    jwt: str | None = None
    claims: NestAuthClaims = field(default_factory=NestAuthClaims)
    error: dict | None = None


@dataclass
class NestEnvironment:
    """Class to describe a Nest environment."""

    name: str
    client_id: str
    host: str
