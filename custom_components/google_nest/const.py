"""Constants for Google Nest integration."""
from __future__ import annotations

import logging

CONF_ACCOUNT_TYPE: str = "account_type"
CONF_COOKIES: str = "cookies"
CONF_ISSUE_TOKEN: str = "issue_token"
CONF_REFRESH_TOKEN: str = "refresh_token"
CONF_SAVE_RESPONSES: str = "save_responses"
CONF_TIMEOUT: str = "timeout"

DEFAULT_SAVE_RESPONSES: bool = False

DOMAIN: str = "google_nest"

LOGGER: logging.Logger = logging.getLogger(__package__)

VALUES_SCAN_INTERVAL: list[int] = [30, 60, 120, 300, 600]
VALUES_TIMEOUT: list[int] = [10, 15, 30, 45, 60]

DEFAULT_SCAN_INTERVAL: int = VALUES_SCAN_INTERVAL[2]
DEFAULT_TIMEOUT: int = VALUES_TIMEOUT[0]
