"""SkyPing Telegram weather bot entry point."""

from __future__ import annotations

import logging
import sys

import httpx
from telegram import BotCommand
from telegram.ext import Application

from config import Settings, load_settings
from db.database import close_db, init_db
from handlers import register_all_handlers
from jobs.scheduled import register_jobs

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand("start", "Welcome and default weather"),
    BotCommand("weather", "Search weather for a city"),
    BotCommand("forecast", "Multi-day forecast (1–7 days)"),
    BotCommand("add", "Save a city to your list"),
    BotCommand("list", "Show saved cities"),
    BotCommand("remove", "Remove a saved city"),
    BotCommand("all", "Weather for all saved cities"),
    BotCommand("subscribe", "Daily weather for a city"),
    BotCommand("unsubscribe", "Stop daily weather"),
    BotCommand("alerts", "Rain alerts on/off for saved cities"),
    BotCommand("settime", "Set daily send time (HH:MM)"),
    BotCommand("settimezone", "Set chat timezone"),
    BotCommand("units", "metric or imperial"),
    BotCommand("language", "Change language"),
]


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        level=getattr(logging, level, logging.INFO),
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def _post_init(application: Application) -> None:
    """Startup hook: DB, HTTP client, bot commands."""
    settings: Settings = application.bot_data["settings"]
    await init_db(settings.db_path)

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "SkyPingBot/1.0"},
        follow_redirects=True,
    )
    application.bot_data["http_client"] = client

    await application.bot.set_my_commands(BOT_COMMANDS)
    logger.info("SkyPing started")


async def _post_shutdown(application: Application) -> None:
    """Graceful shutdown: close HTTP client and database."""
    client: httpx.AsyncClient | None = application.bot_data.get("http_client")
    if client is not None:
        await client.aclose()
        logger.info("HTTP client closed")
    await close_db()
    logger.info("SkyPing shut down")


def build_application(settings: Settings) -> Application:
    """Construct the telegram Application with handlers and jobs."""
    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    application.bot_data["settings"] = settings
    register_all_handlers(application)
    register_jobs(application)
    return application


def main() -> None:
    """Load settings and run polling until interrupted."""
    settings = load_settings()
    _configure_logging(settings.log_level)
    application = build_application(settings)
    logger.info("Starting polling…")
    application.run_polling(
        allowed_updates=["message", "callback_query", "inline_query"]
    )


if __name__ == "__main__":
    main()
