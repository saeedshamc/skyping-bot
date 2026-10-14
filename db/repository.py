"""All SQL queries for users/chats, cities, and subscriptions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from db.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class ChatRecord:
    """Persisted chat settings."""

    chat_id: int
    chat_type: str
    units: str
    timezone: str
    send_time: str
    language: str
    active: bool
    last_sent_date: str | None
    rain_alerts: bool = False
    rain_threshold: int = 60
    last_rain_alert_date: str | None = None


@dataclass
class CityRecord:
    """A city saved for a chat."""

    id: int
    chat_id: int
    name: str
    admin1: str | None
    country: str | None
    country_code: str | None
    latitude: float
    longitude: float


def _chat_from_row(row: Any) -> ChatRecord:
    keys = set(row.keys())
    return ChatRecord(
        chat_id=row["chat_id"],
        chat_type=row["chat_type"],
        units=row["units"],
        timezone=row["timezone"],
        send_time=row["send_time"],
        language=row["language"],
        active=bool(row["active"]),
        last_sent_date=row["last_sent_date"],
        rain_alerts=bool(row["rain_alerts"]) if "rain_alerts" in keys else False,
        rain_threshold=int(row["rain_threshold"]) if "rain_threshold" in keys else 60,
        last_rain_alert_date=(
            row["last_rain_alert_date"] if "last_rain_alert_date" in keys else None
        ),
    )


def _city_from_row(row: Any) -> CityRecord:
    return CityRecord(
        id=row["id"],
        chat_id=row["chat_id"],
        name=row["name"],
        admin1=row["admin1"],
        country=row["country"],
        country_code=row["country_code"],
        latitude=row["latitude"],
        longitude=row["longitude"],
    )


async def upsert_chat(
    chat_id: int,
    chat_type: str,
    *,
    timezone: str,
    send_time: str,
    language: str = "en",
    units: str = "metric",
) -> ChatRecord:
    """Insert a chat or return the existing record (settings preserved)."""
    db = get_db()
    existing = await get_chat(chat_id)
    if existing:
        if existing.chat_type != chat_type:
            await db.execute(
                "UPDATE chats SET chat_type = ? WHERE chat_id = ?",
                (chat_type, chat_id),
            )
            await db.commit()
            existing.chat_type = chat_type
        return existing

    await db.execute(
        """
        INSERT INTO chats (chat_id, chat_type, units, timezone, send_time, language, active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (chat_id, chat_type, units, timezone, send_time, language),
    )
    await db.commit()
    chat = await get_chat(chat_id)
    assert chat is not None
    return chat


async def get_chat(chat_id: int) -> ChatRecord | None:
    """Fetch a single chat by id."""
    db = get_db()
    async with db.execute("SELECT * FROM chats WHERE chat_id = ?", (chat_id,)) as cur:
        row = await cur.fetchone()
    return _chat_from_row(row) if row else None


async def set_units(chat_id: int, units: str) -> None:
    """Update temperature/wind unit preference."""
    db = get_db()
    await db.execute("UPDATE chats SET units = ? WHERE chat_id = ?", (units, chat_id))
    await db.commit()


async def set_language(chat_id: int, language: str) -> None:
    """Update UI language for a chat."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET language = ? WHERE chat_id = ?", (language, chat_id)
    )
    await db.commit()


async def set_send_time(chat_id: int, send_time: str) -> None:
    """Update daily send time (HH:MM)."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET send_time = ? WHERE chat_id = ?", (send_time, chat_id)
    )
    await db.commit()


async def set_timezone(chat_id: int, timezone: str) -> None:
    """Update IANA timezone for a chat."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET timezone = ? WHERE chat_id = ?", (timezone, chat_id)
    )
    await db.commit()


async def set_active(chat_id: int, active: bool) -> None:
    """Activate or deactivate scheduled posts for a chat."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET active = ? WHERE chat_id = ?", (1 if active else 0, chat_id)
    )
    await db.commit()


async def set_last_sent_date(chat_id: int, date_str: str) -> None:
    """Record the local date of the last daily post."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET last_sent_date = ? WHERE chat_id = ?", (date_str, chat_id)
    )
    await db.commit()


async def count_saved_cities(chat_id: int) -> int:
    """Return how many cities a chat has saved."""
    db = get_db()
    async with db.execute(
        "SELECT COUNT(*) AS c FROM saved_cities WHERE chat_id = ?", (chat_id,)
    ) as cur:
        row = await cur.fetchone()
    return int(row["c"]) if row else 0


async def add_saved_city(
    chat_id: int,
    *,
    name: str,
    admin1: str | None,
    country: str | None,
    country_code: str | None,
    latitude: float,
    longitude: float,
) -> CityRecord:
    """Save a city for a chat (idempotent on lat/lon)."""
    db = get_db()
    await db.execute(
        """
        INSERT INTO saved_cities
            (chat_id, name, admin1, country, country_code, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id, latitude, longitude) DO UPDATE SET
            name = excluded.name,
            admin1 = excluded.admin1,
            country = excluded.country,
            country_code = excluded.country_code
        """,
        (chat_id, name, admin1, country, country_code, latitude, longitude),
    )
    await db.commit()
    city = await get_city_by_coords(chat_id, latitude, longitude)
    assert city is not None
    return city


async def get_city_by_id(city_id: int) -> CityRecord | None:
    """Fetch a saved city by primary key."""
    db = get_db()
    async with db.execute("SELECT * FROM saved_cities WHERE id = ?", (city_id,)) as cur:
        row = await cur.fetchone()
    return _city_from_row(row) if row else None


async def get_city_by_coords(
    chat_id: int, latitude: float, longitude: float
) -> CityRecord | None:
    """Fetch a saved city by chat and coordinates."""
    db = get_db()
    async with db.execute(
        """
        SELECT * FROM saved_cities
        WHERE chat_id = ? AND latitude = ? AND longitude = ?
        """,
        (chat_id, latitude, longitude),
    ) as cur:
        row = await cur.fetchone()
    return _city_from_row(row) if row else None


async def list_saved_cities(chat_id: int) -> list[CityRecord]:
    """List all cities saved for a chat."""
    db = get_db()
    async with db.execute(
        "SELECT * FROM saved_cities WHERE chat_id = ? ORDER BY name COLLATE NOCASE",
        (chat_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_city_from_row(r) for r in rows]


async def remove_saved_city(chat_id: int, city_id: int) -> bool:
    """Delete a saved city (and cascading subscriptions)."""
    db = get_db()
    cursor = await db.execute(
        "DELETE FROM saved_cities WHERE id = ? AND chat_id = ?", (city_id, chat_id)
    )
    await db.commit()
    return cursor.rowcount > 0


async def add_subscription(chat_id: int, city_id: int) -> None:
    """Subscribe a chat to daily posts for a saved city."""
    db = get_db()
    await db.execute(
        """
        INSERT OR IGNORE INTO subscriptions (chat_id, city_id) VALUES (?, ?)
        """,
        (chat_id, city_id),
    )
    await db.execute(
        "UPDATE chats SET active = 1 WHERE chat_id = ?", (chat_id,)
    )
    await db.commit()


async def remove_subscription(chat_id: int, city_id: int) -> bool:
    """Unsubscribe a chat from a city."""
    db = get_db()
    cursor = await db.execute(
        "DELETE FROM subscriptions WHERE chat_id = ? AND city_id = ?",
        (chat_id, city_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def list_subscribed_cities(chat_id: int) -> list[CityRecord]:
    """List cities a chat is subscribed to for daily posts."""
    db = get_db()
    async with db.execute(
        """
        SELECT sc.* FROM saved_cities sc
        INNER JOIN subscriptions s ON s.city_id = sc.id
        WHERE s.chat_id = ?
        ORDER BY sc.name COLLATE NOCASE
        """,
        (chat_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_city_from_row(r) for r in rows]


async def list_due_chats() -> list[ChatRecord]:
    """Return all active chats that have at least one subscription."""
    db = get_db()
    async with db.execute(
        """
        SELECT DISTINCT c.* FROM chats c
        INNER JOIN subscriptions s ON s.chat_id = c.chat_id
        WHERE c.active = 1
        """
    ) as cur:
        rows = await cur.fetchall()
    return [_chat_from_row(r) for r in rows]


async def set_rain_alerts(
    chat_id: int,
    *,
    enabled: bool | None = None,
    threshold: int | None = None,
) -> None:
    """Update rain-alert preferences for a chat."""
    db = get_db()
    if enabled is not None and threshold is not None:
        await db.execute(
            "UPDATE chats SET rain_alerts = ?, rain_threshold = ? WHERE chat_id = ?",
            (1 if enabled else 0, threshold, chat_id),
        )
    elif enabled is not None:
        await db.execute(
            "UPDATE chats SET rain_alerts = ? WHERE chat_id = ?",
            (1 if enabled else 0, chat_id),
        )
    elif threshold is not None:
        await db.execute(
            "UPDATE chats SET rain_threshold = ? WHERE chat_id = ?",
            (threshold, chat_id),
        )
    await db.commit()


async def set_last_rain_alert_date(chat_id: int, date_str: str) -> None:
    """Record the local date of the last rain alert."""
    db = get_db()
    await db.execute(
        "UPDATE chats SET last_rain_alert_date = ? WHERE chat_id = ?",
        (date_str, chat_id),
    )
    await db.commit()


async def list_rain_alert_chats() -> list[ChatRecord]:
    """Return chats with rain alerts enabled."""
    db = get_db()
    async with db.execute(
        "SELECT * FROM chats WHERE rain_alerts = 1 AND active = 1"
    ) as cur:
        rows = await cur.fetchall()
    return [_chat_from_row(r) for r in rows]
