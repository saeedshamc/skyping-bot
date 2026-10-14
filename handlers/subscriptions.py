"""Subscription, schedule, timezone, and units handlers."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import Settings
from db import repository as repo
from handlers.weather import ACTION_SUBSCRIBE, _reply_search_results
from i18n.strings import t
from services.geocoding import City
from utils.helpers import (
    ensure_chat,
    escape_html,
    format_place,
    get_lang,
    is_valid_time,
    user_is_admin,
)
from utils.keyboards import saved_cities_keyboard

logger = logging.getLogger(__name__)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe the chat to a daily weather post for a city."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await update.effective_message.reply_text(t(lang, "admin_only"))
        return

    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.effective_message.reply_text(
            t(lang, "need_city_arg", example="/subscribe Tehran"),
            parse_mode=ParseMode.HTML,
        )
        return
    await _reply_search_results(update, context, query, action=ACTION_SUBSCRIBE)


async def finish_subscribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    city: City,
) -> None:
    """Save city + create subscription after inline pick."""
    query = update.callback_query
    chat_id = await ensure_chat(update, context)
    if chat_id is None or query is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await query.edit_message_text(t(lang, "admin_only"))
        return

    settings: Settings = context.application.bot_data["settings"]
    place = format_place(city.name, city.admin1, city.country, city.country_code)

    count = await repo.count_saved_cities(chat_id)
    existing = await repo.get_city_by_coords(chat_id, city.latitude, city.longitude)
    if existing is None and count >= settings.max_cities_per_user:
        await query.edit_message_text(
            t(lang, "city_limit", max=settings.max_cities_per_user)
        )
        return

    saved = await repo.add_saved_city(
        chat_id,
        name=city.name,
        admin1=city.admin1,
        country=city.country,
        country_code=city.country_code,
        latitude=city.latitude,
        longitude=city.longitude,
    )

    before = await repo.list_subscribed_cities(chat_id)
    already = any(c.id == saved.id for c in before)
    await repo.add_subscription(chat_id, saved.id)

    if already:
        await query.edit_message_text(
            t(lang, "subscribe_already", place=escape_html(place)),
            parse_mode=ParseMode.HTML,
        )
    else:
        await query.edit_message_text(
            t(lang, "subscribe_ok", place=escape_html(place)),
            parse_mode=ParseMode.HTML,
        )


async def unsubscribe_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show subscribed cities for removal."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await update.effective_message.reply_text(t(lang, "admin_only"))
        return

    cities = await repo.list_subscribed_cities(chat_id)
    if not cities:
        await update.effective_message.reply_text(t(lang, "no_subscriptions"))
        return
    await update.effective_message.reply_text(
        t(lang, "unsubscribe_title"),
        reply_markup=saved_cities_keyboard(cities, action="unsub"),
    )


async def unsubscribe_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Remove a subscription."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await query.edit_message_text(t(lang, "admin_only"))
        return

    _, _, id_str = query.data.partition(":")
    try:
        city_id = int(id_str)
    except ValueError:
        return

    city = await repo.get_city_by_id(city_id)
    if city is None or city.chat_id != chat_id:
        await query.edit_message_text(t(lang, "expired_selection"))
        return

    place = format_place(city.name, city.admin1, city.country, city.country_code)
    await repo.remove_subscription(chat_id, city_id)
    await query.edit_message_text(
        t(lang, "unsubscribed", place=escape_html(place)),
        parse_mode=ParseMode.HTML,
    )


async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set daily send time for the chat."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await update.effective_message.reply_text(t(lang, "admin_only"))
        return

    if not context.args or not is_valid_time(context.args[0]):
        await update.effective_message.reply_text(t(lang, "settime_usage"))
        return

    time_str = context.args[0].strip()
    await repo.set_send_time(chat_id, time_str)
    chat = await repo.get_chat(chat_id)
    tz = chat.timezone if chat else ""
    await update.effective_message.reply_text(
        t(lang, "settime_ok", time=escape_html(time_str), tz=escape_html(tz)),
        parse_mode=ParseMode.HTML,
    )


async def settimezone_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Set IANA timezone for the chat."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await update.effective_message.reply_text(t(lang, "admin_only"))
        return

    if not context.args:
        await update.effective_message.reply_text(
            t(lang, "settimezone_usage"), parse_mode=ParseMode.HTML
        )
        return

    tz_name = context.args[0].strip()
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        await update.effective_message.reply_text(
            t(lang, "settimezone_invalid", tz=escape_html(tz_name)),
            parse_mode=ParseMode.HTML,
        )
        return

    await repo.set_timezone(chat_id, tz_name)
    await update.effective_message.reply_text(
        t(lang, "settimezone_ok", tz=escape_html(tz_name)),
        parse_mode=ParseMode.HTML,
    )


async def units_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set metric or imperial units."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not context.args or context.args[0].lower() not in ("metric", "imperial"):
        await update.effective_message.reply_text(t(lang, "units_invalid"))
        return

    units = context.args[0].lower()
    await repo.set_units(chat_id, units)
    await update.effective_message.reply_text(
        t(lang, "units_set", units=escape_html(units)),
        parse_mode=ParseMode.HTML,
    )


def register_subscription_handlers(application: Application) -> None:
    """Register subscription and preference handlers."""
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("settime", settime_command))
    application.add_handler(CommandHandler("settimezone", settimezone_command))
    application.add_handler(CommandHandler("units", units_command))
    application.add_handler(
        CallbackQueryHandler(unsubscribe_callback, pattern=r"^unsub:")
    )
