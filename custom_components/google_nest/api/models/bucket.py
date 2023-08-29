"""Models used by Nest."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Bucket:
    """Class that reflects a Nest API response."""

    object_key: str
    object_revision: str
    object_timestamp: str
    value: Any
