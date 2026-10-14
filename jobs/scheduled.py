"""Daily weather sender for chats and configured channels."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import Bot
from telegram.error import Forbidden, BadRequest, TelegramError
from telegram.ext import Application, ContextTypes

from config import ChannelCity, Settings
from db import repository as repo
from i18n.strings import t
from services.formatter import (
    format_multi_weather,
    format_rain_alert,
    format_weather_block,
)
from services.weather import WeatherError, fetch_weather
from utils.helpers import format_place

logger = logging.getLogger(__name__)

# Telegram error substrings that mean the bot can no longer message the chat.
_DEACTIVATE_HINTS = (
    "bot was blocked",
    "bot was kicked",
    "chat not found",
    "forbidden",
    "deactivated",
    "have no rights",
    "not enough rights",
    "group chat was upgraded",
)


def _should_deactivate(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(h in text for h in _DEACTIVATE_HINTS)


def _local_now(timezone_name: str) -> datetime | None:
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        logger.warning("Invalid timezone %r; skipping chat", timezone_name)
        return None
    return datetime.now(tz)


def _is_due(chat: repo.ChatRecord, now: datetime) -> bool:
    """Return True if local time matches send_time and we have not sent today."""
    hh, mm = chat.send_time.split(":")
    if now.hour != int(hh) or now.minute != int(mm):
        return False
    today = now.date().isoformat()
    return chat.last_sent_date != today


async def _build_cities_message(
    client,
    cities: list,
    *,
    units: str,
    lang: str,
    header_key: str = "daily_header",
) -> str | None:
    async def _one(city) -> str | None:
        try:
            weather = await fetch_weather(
                client, city.latitude, city.longitude, units=units
            )
            return format_weather_block(
                weather,
                name=city.name,
                admin1=getattr(city, "admin1", None),
                country=getattr(city, "country", None),
                country_code=getattr(city, "country_code", None),
                lang=lang,
            )
        except WeatherError:
            logger.warning("Scheduled weather fetch failed for %s", getattr(city, "name", city))
            return None

    results = await asyncio.gather(*[_one(c) for c in cities])
    blocks = [b for b in results if b]
    if not blocks:
        return None
    text = format_multi_weather(blocks, lang=lang, header_key=header_key)
    if len(text) > 4000:
        text = text[:3990] + "…"
    return text


async def _send_or_deactivate(
    bot: Bot,
    chat_id: int,
    text: str,
) -> bool:
    """Send a message; deactivate chat on kick/block. Return success."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        return True
    except (Forbidden, BadRequest) as exc:
        if _should_deactivate(exc):
            logger.warning(
                "Deactivating chat %s after send failure: %s", chat_id, exc
            )
            await repo.set_active(chat_id, False)
        else:
            logger.error("Failed to send daily post to %s: %s", chat_id, exc)
        return False
    except TelegramError as exc:
        if _should_deactivate(exc):
            logger.warning(
                "Deactivating chat %s after TelegramError: %s", chat_id, exc
            )
            await repo.set_active(chat_id, False)
        else:
            logger.error("Telegram error sending to %s: %s", chat_id, exc)
        return False


async def check_and_send_daily(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: send due daily posts for subscribed chats."""
    client = context.application.bot_data["http_client"]
    chats = await repo.list_due_chats()
    for chat in chats:
        now = _local_now(chat.timezone)
        if now is None or not _is_due(chat, now):
            continue

        cities = await repo.list_subscribed_cities(chat.chat_id)
        if not cities:
            continue

        text = await _build_cities_message(
            client,
            cities,
            units=chat.units,
            lang=chat.language,
            header_key="daily_header",
        )
        if not text:
            continue

        ok = await _send_or_deactivate(context.bot, chat.chat_id, text)
        if ok:
            await repo.set_last_sent_date(chat.chat_id, now.date().isoformat())
            logger.info("Sent daily weather to chat %s", chat.chat_id)


async def send_channel_daily(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily posts to statically configured channels."""
    settings: Settings = context.application.bot_data["settings"]
    if not settings.channel_ids or not settings.channel_cities:
        return

    # Use DEFAULT_TIMEZONE + DEFAULT_SEND_TIME for channels.
    now = _local_now(settings.default_timezone)
    if now is None:
        return
    hh, mm = settings.default_send_time.split(":")
    if now.hour != int(hh) or now.minute != int(mm):
        return

    # Deduplicate via a synthetic key in bot_data for the local date.
    today = now.date().isoformat()
    sent_key = "channel_last_sent_date"
    if context.application.bot_data.get(sent_key) == today:
        return

    client = context.application.bot_data["http_client"]

    class _City:
        def __init__(self, c: ChannelCity) -> None:
            self.name = c.name
            self.latitude = c.latitude
            self.longitude = c.longitude
            self.admin1 = None
            self.country = None
            self.country_code = None

    cities = [_City(c) for c in settings.channel_cities]
    text = await _build_cities_message(
        client,
        cities,
        units="metric",
        lang=settings.default_language,
        header_key="daily_header",
    )
    if not text:
        return

    any_ok = False
    for channel in settings.channel_ids:
        try:
            await context.bot.send_message(
                chat_id=channel, text=text, parse_mode="HTML"
            )
            any_ok = True
            logger.info("Sent daily weather to channel %s", channel)
        except TelegramError as exc:
            logger.warning("Failed to send to channel %s: %s", channel, exc)

    if any_ok:
        context.application.bot_data[sent_key] = today


async def check_rain_alerts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Notify chats when today's precip chance exceeds their threshold."""
    client = context.application.bot_data["http_client"]
    chats = await repo.list_rain_alert_chats()
    for chat in chats:
        now = _local_now(chat.timezone)
        if now is None:
            continue
        today = now.date().isoformat()
        if chat.last_rain_alert_date == today:
            continue

        # Morning–evening window so we don't alert at midnight with stale odds.
        if now.hour < 6 or now.hour > 21:
            continue

        cities = await repo.list_saved_cities(chat.chat_id)
        if not cities:
            continue

        alert_blocks: list[str] = []
        for city in cities:
            try:
                weather = await fetch_weather(
                    client, city.latitude, city.longitude, units=chat.units
                )
            except WeatherError:
                continue
            precip = weather.precip_probability
            if precip is None or precip < chat.rain_threshold:
                continue
            place = format_place(
                city.name, city.admin1, city.country, city.country_code
            )
            alert_blocks.append(
                format_rain_alert(
                    place=place,
                    precip_probability=precip,
                    threshold=chat.rain_threshold,
                    lang=chat.language,
                )
            )

        if not alert_blocks:
            continue

        text = "\n\n".join(alert_blocks)
        if len(text) > 4000:
            text = text[:3990] + "…"

        ok = await _send_or_deactivate(context.bot, chat.chat_id, text)
        if ok:
            await repo.set_last_rain_alert_date(chat.chat_id, today)
            logger.info("Sent rain alert to chat %s", chat.chat_id)


def register_jobs(application: Application) -> None:
    """Schedule the per-minute checker (survives restarts via DB state)."""
    jq = application.job_queue
    if jq is None:
        logger.error(
            "JobQueue is not available. Install python-telegram-bot[job-queue]."
        )
        return
    jq.run_repeating(check_and_send_daily, interval=60, first=10, name="daily_chats")
    jq.run_repeating(send_channel_daily, interval=60, first=15, name="daily_channels")
    jq.run_repeating(check_rain_alerts, interval=30 * 60, first=45, name="rain_alerts")
    logger.info("Scheduled daily weather and rain-alert jobs")
