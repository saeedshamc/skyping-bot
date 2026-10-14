"""City search, weather display, and selection callbacks."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db import repository as repo
from i18n.strings import t
from services.formatter import format_daily_forecast, format_weather_block
from services.geocoding import City, GeocodingError, GeocodingTimeout, search_cities
from services.weather import (
    WeatherError,
    WeatherTimeout,
    fetch_daily_forecast,
    fetch_weather,
)
from utils.helpers import ensure_chat, escape_html, get_lang
from utils.keyboards import city_search_keyboard

logger = logging.getLogger(__name__)

# Actions stored in callback_data prefix
ACTION_WEATHER = "wx"
ACTION_ADD = "add"
ACTION_SUBSCRIBE = "sub"
ACTION_FORECAST = "fc"
DEFAULT_FORECAST_DAYS = 3


def _store_search_results(context: ContextTypes.DEFAULT_TYPE, cities: list[City]) -> None:
    """Cache geocoding hits in user_data keyed by Open-Meteo id."""
    cache: dict[int, dict[str, Any]] = context.user_data.setdefault("geo_cache", {})
    for city in cities:
        cache[city.id] = city.to_dict()


def _get_cached_city(context: ContextTypes.DEFAULT_TYPE, geo_id: int) -> City | None:
    cache: dict[int, dict[str, Any]] = context.user_data.get("geo_cache") or {}
    data = cache.get(geo_id)
    if not data:
        return None
    return City.from_dict(data)


async def _reply_search_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    *,
    action: str,
) -> None:
    """Run geocoding and show an inline selection keyboard."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    client = context.application.bot_data["http_client"]

    status = await update.effective_message.reply_text(
        t(lang, "searching", query=escape_html(query)),
        parse_mode=ParseMode.HTML,
    )
    try:
        cities = await search_cities(client, query, language=lang)
    except GeocodingTimeout:
        await status.edit_text(t(lang, "timeout"))
        return
    except GeocodingError:
        await status.edit_text(t(lang, "api_error"))
        return

    if not cities:
        await status.edit_text(
            t(lang, "no_results", query=escape_html(query)),
            parse_mode=ParseMode.HTML,
        )
        return

    _store_search_results(context, cities)
    await status.edit_text(
        t(lang, "select_city"),
        reply_markup=city_search_keyboard(
            [c.to_dict() for c in cities],
            action=action,
        ),
    )


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weather <city>."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.effective_message.reply_text(
            t(lang, "need_city_arg", example="/weather Tehran"),
            parse_mode=ParseMode.HTML,
        )
        return
    await _reply_search_results(update, context, query, action=ACTION_WEATHER)


def _parse_forecast_args(args: list[str] | None) -> tuple[int, str]:
    """Parse `/forecast [days] <city>` into (days, city_query)."""
    if not args:
        return DEFAULT_FORECAST_DAYS, ""
    if args[0].isdigit():
        days = max(1, min(7, int(args[0])))
        return days, " ".join(args[1:]).strip()
    return DEFAULT_FORECAST_DAYS, " ".join(args).strip()


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /forecast [1-7] <city>."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    days, query = _parse_forecast_args(context.args)
    if not query:
        await update.effective_message.reply_text(
            t(lang, "forecast_usage"),
            parse_mode=ParseMode.HTML,
        )
        return
    context.user_data["forecast_days"] = days
    await _reply_search_results(update, context, query, action=ACTION_FORECAST)


async def send_forecast_for_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    city: City,
    *,
    days: int = DEFAULT_FORECAST_DAYS,
    edit: bool = False,
) -> None:
    """Fetch and send a multi-day forecast for a city."""
    message = update.effective_message
    if message is None and update.callback_query:
        message = update.callback_query.message
    if message is None:
        return

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    chat = await repo.get_chat(chat_id)
    units = chat.units if chat else "metric"
    client = context.application.bot_data["http_client"]

    try:
        forecast = await fetch_daily_forecast(
            client, city.latitude, city.longitude, days=days, units=units
        )
    except WeatherTimeout:
        text = t(lang, "timeout")
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await message.reply_text(text)
        return
    except WeatherError:
        text = t(lang, "api_error")
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await message.reply_text(text)
        return

    block = format_daily_forecast(
        forecast,
        name=city.name,
        admin1=city.admin1,
        country=city.country,
        country_code=city.country_code,
        lang=lang,
    )
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(block, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(block, parse_mode=ParseMode.HTML)


async def plain_text_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Treat plain text in private chats as a city search."""
    if update.effective_chat is None or update.effective_message is None:
        return
    if update.effective_chat.type != ChatType.PRIVATE:
        return
    text = (update.effective_message.text or "").strip()
    if not text or text.startswith("/"):
        return
    await _reply_search_results(update, context, text, action=ACTION_WEATHER)


async def send_weather_for_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    city: City,
    *,
    edit: bool = False,
) -> None:
    """Fetch and send weather for an exact lat/lon city."""
    message = update.effective_message
    if message is None and update.callback_query:
        message = update.callback_query.message
    if message is None:
        return

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    chat = await repo.get_chat(chat_id)
    units = chat.units if chat else "metric"
    client = context.application.bot_data["http_client"]

    try:
        weather = await fetch_weather(
            client, city.latitude, city.longitude, units=units
        )
    except WeatherTimeout:
        text = t(lang, "timeout")
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await message.reply_text(text)
        return
    except WeatherError:
        text = t(lang, "api_error")
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await message.reply_text(text)
        return

    block = format_weather_block(
        weather,
        name=city.name,
        admin1=city.admin1,
        country=city.country,
        country_code=city.country_code,
        lang=lang,
    )
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(block, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(block, parse_mode=ParseMode.HTML)


async def city_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline city selection for weather / add / subscribe."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()

    action, _, id_str = query.data.partition(":")
    try:
        geo_id = int(id_str)
    except ValueError:
        return

    city = _get_cached_city(context, geo_id)
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if city is None:
        await query.edit_message_text(t(lang, "expired_selection"))
        return

    if action == ACTION_WEATHER:
        await send_weather_for_city(update, context, city, edit=True)
        return

    if action == ACTION_FORECAST:
        days = int(context.user_data.get("forecast_days") or DEFAULT_FORECAST_DAYS)
        await send_forecast_for_city(update, context, city, days=days, edit=True)
        return

    if action == ACTION_ADD:
        from handlers.cities import finish_add_city

        await finish_add_city(update, context, city)
        return

    if action == ACTION_SUBSCRIBE:
        from handlers.subscriptions import finish_subscribe

        await finish_subscribe(update, context, city)
        return


async def saved_city_weather_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle tapping a city from /list."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()

    _, _, id_str = query.data.partition(":")
    try:
        city_id = int(id_str)
    except ValueError:
        return

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    record = await repo.get_city_by_id(city_id)
    if record is None or record.chat_id != chat_id:
        await query.edit_message_text(t(lang, "expired_selection"))
        return

    city = City(
        id=record.id,
        name=record.name,
        latitude=record.latitude,
        longitude=record.longitude,
        country=record.country,
        country_code=record.country_code,
        admin1=record.admin1,
    )
    await send_weather_for_city(update, context, city, edit=True)


def register_weather_handlers(application: Application) -> None:
    """Register weather search and selection handlers."""
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(
        CallbackQueryHandler(
            city_select_callback,
            pattern=rf"^({ACTION_WEATHER}|{ACTION_ADD}|{ACTION_SUBSCRIBE}|{ACTION_FORECAST}):",
        )
    )
    application.add_handler(
        CallbackQueryHandler(saved_city_weather_callback, pattern=r"^list:")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, plain_text_city)
    )
