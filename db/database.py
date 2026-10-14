"""SQLite connection helper and schema initialization."""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

_db: aiosqlite.Connection | None = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chats (
    chat_id        INTEGER PRIMARY KEY,
    chat_type      TEXT    NOT NULL,
    units          TEXT    NOT NULL DEFAULT 'metric',
    timezone       TEXT    NOT NULL,
    send_time      TEXT    NOT NULL,
    language       TEXT    NOT NULL DEFAULT 'en',
    active         INTEGER NOT NULL DEFAULT 1,
    last_sent_date TEXT
);

CREATE TABLE IF NOT EXISTS saved_cities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    admin1       TEXT,
    country      TEXT,
    country_code TEXT,
    latitude     REAL    NOT NULL,
    longitude    REAL    NOT NULL,
    UNIQUE (chat_id, latitude, longitude),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    city_id INTEGER NOT NULL,
    UNIQUE (chat_id, city_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (city_id) REFERENCES saved_cities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saved_cities_chat ON saved_cities(chat_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_chat ON subscriptions(chat_id);
"""


async def init_db(db_path: Path) -> aiosqlite.Connection:
    """Open the database, enable foreign keys, and apply the schema."""
    global _db
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(db_path)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA foreign_keys = ON")
    await _db.executescript(SCHEMA_SQL)
    await _migrate(_db)
    await _db.commit()
    logger.info("Database initialized at %s", db_path)
    return _db


async def _migrate(conn: aiosqlite.Connection) -> None:
    """Apply lightweight additive migrations for existing databases."""
    async with conn.execute("PRAGMA table_info(chats)") as cursor:
        columns = {row["name"] for row in await cursor.fetchall()}
    if "language" not in columns:
        await conn.execute(
            "ALTER TABLE chats ADD COLUMN language TEXT NOT NULL DEFAULT 'en'"
        )
        logger.info("Migrated chats table: added language column")


def get_db() -> aiosqlite.Connection:
    """Return the shared database connection."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def close_db() -> None:
    """Close the shared database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database connection closed")
