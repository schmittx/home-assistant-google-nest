"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field

from .bucket import Bucket


@dataclass
class KryptoniteBucketValue:
    """Temperature Sensor values."""

    battery_level: int
    current_temperature: float
    last_updated_at: int
    model: str
    serial_number: str
    structure_id: str
    where_id: str


@dataclass
class KryptoniteBucket(Bucket):
    """Class that reflects a Nest API response."""

    value: KryptoniteBucketValue = field(default_factory=KryptoniteBucketValue)

@dataclass
class Devices:
    """Class that reflects a Nest API response."""

    structures: Structure = field(default_factory=Structure)
