"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
_SUPPORTED_LANGUAGES = frozenset({"en", "fa"})


@dataclass(frozen=True)
class ChannelCity:
    """A city configured for static channel daily posts."""

    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings for SkyPing."""

    bot_token: str
    default_city_name: str
    default_city_lat: float
    default_city_lon: float
    default_timezone: str
    default_send_time: str
    default_language: str
    max_cities_per_user: int
    channel_ids: list[int | str] = field(default_factory=list)
    channel_cities: list[ChannelCity] = field(default_factory=list)
    db_path: Path = Path("storage/skyping.db")
    log_level: str = "INFO"


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and set {name}."
        )
    return value


def _parse_float(name: str, default: str | None = None) -> float:
    raw = os.getenv(name, default if default is not None else "").strip()
    if not raw:
        raise SystemExit(f"Missing required environment variable: {name}.")
    try:
        return float(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid float for {name}: {raw!r}") from exc


def _parse_int(name: str, default: str) -> int:
    raw = os.getenv(name, default).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer for {name}: {raw!r}") from exc
    if value < 1:
        raise SystemExit(f"{name} must be >= 1, got {value}.")
    return value


def _parse_send_time(raw: str) -> str:
    if not _TIME_RE.match(raw):
        raise SystemExit(
            f"Invalid DEFAULT_SEND_TIME={raw!r}. Expected HH:MM (24-hour)."
        )
    return raw


def _parse_language(raw: str) -> str:
    lang = raw.strip().lower()
    if lang not in _SUPPORTED_LANGUAGES:
        raise SystemExit(
            f"Invalid DEFAULT_LANGUAGE={raw!r}. Supported: {', '.join(sorted(_SUPPORTED_LANGUAGES))}."
        )
    return lang


def _parse_channel_ids(raw: str) -> list[int | str]:
    if not raw.strip():
        return []
    result: list[int | str] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if item.lstrip("-").isdigit():
            result.append(int(item))
        else:
            result.append(item.lstrip("@"))
    return result


def _parse_channel_cities(raw: str) -> list[ChannelCity]:
    """Parse CHANNEL_CITIES like 'Tehran:35.69:51.39,Isfahan:32.65:51.67'."""
    if not raw.strip():
        return []
    cities: list[ChannelCity] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        pieces = item.split(":")
        if len(pieces) != 3:
            raise SystemExit(
                f"Invalid CHANNEL_CITIES entry {item!r}. "
                "Expected Name:lat:lon"
            )
        name, lat_s, lon_s = pieces
        try:
            cities.append(
                ChannelCity(
                    name=name.strip(),
                    latitude=float(lat_s),
                    longitude=float(lon_s),
                )
            )
        except ValueError as exc:
            raise SystemExit(f"Invalid lat/lon in CHANNEL_CITIES entry {item!r}") from exc
    return cities


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    """Load and validate settings from the environment."""
    if env_file:
        load_dotenv(env_file)

    send_time = _parse_send_time(os.getenv("DEFAULT_SEND_TIME", "07:30").strip())
    language = _parse_language(os.getenv("DEFAULT_LANGUAGE", "en"))
    db_path = Path(os.getenv("DB_PATH", "storage/skyping.db").strip())
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    return Settings(
        bot_token=_require("BOT_TOKEN"),
        default_city_name=os.getenv("DEFAULT_CITY_NAME", "Tehran").strip() or "Tehran",
        default_city_lat=_parse_float("DEFAULT_CITY_LAT", "35.6892"),
        default_city_lon=_parse_float("DEFAULT_CITY_LON", "51.3890"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Asia/Tehran").strip() or "Asia/Tehran",
        default_send_time=send_time,
        default_language=language,
        max_cities_per_user=_parse_int("MAX_CITIES_PER_USER", "10"),
        channel_ids=_parse_channel_ids(os.getenv("CHANNEL_IDS", "")),
        channel_cities=_parse_channel_cities(os.getenv("CHANNEL_CITIES", "")),
        db_path=db_path,
        log_level=log_level,
    )
