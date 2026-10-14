""" /add, /list, /remove, /all handlers. """

from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import Settings
from db import repository as repo
from handlers.weather import ACTION_ADD, _reply_search_results
from i18n.strings import t
from services.formatter import format_multi_weather, format_weather_block
from services.geocoding import City
from services.weather import WeatherError, fetch_weather
from utils.helpers import ensure_chat, escape_html, format_place, get_lang
from utils.keyboards import saved_cities_keyboard

logger = logging.getLogger(__name__)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search and add a city to the user's list."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.effective_message.reply_text(
            t(lang, "need_city_arg", example="/add Tehran"),
            parse_mode=ParseMode.HTML,
        )
        return
    await _reply_search_results(update, context, query, action=ACTION_ADD)


async def finish_add_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    city: City,
) -> None:
    """Persist a selected city after inline pick."""
    query = update.callback_query
    chat_id = await ensure_chat(update, context)
    if chat_id is None or query is None:
        return
    lang = await get_lang(chat_id, context)
    settings: Settings = context.application.bot_data["settings"]
    place = format_place(city.name, city.admin1, city.country, city.country_code)

    existing = await repo.get_city_by_coords(chat_id, city.latitude, city.longitude)
    if existing:
        await query.edit_message_text(
            t(lang, "city_already", place=escape_html(place)),
            parse_mode=ParseMode.HTML,
        )
        return

    count = await repo.count_saved_cities(chat_id)
    if count >= settings.max_cities_per_user:
        await query.edit_message_text(
            t(lang, "city_limit", max=settings.max_cities_per_user)
        )
        return

    await repo.add_saved_city(
        chat_id,
        name=city.name,
        admin1=city.admin1,
        country=city.country,
        country_code=city.country_code,
        latitude=city.latitude,
        longitude=city.longitude,
    )
    await query.edit_message_text(
        t(lang, "city_added", place=escape_html(place)),
        parse_mode=ParseMode.HTML,
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show saved cities as weather buttons."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    cities = await repo.list_saved_cities(chat_id)
    if not cities:
        await update.effective_message.reply_text(t(lang, "no_cities"), parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        t(lang, "list_title"),
        reply_markup=saved_cities_keyboard(cities, action="list"),
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show saved cities with delete buttons."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    cities = await repo.list_saved_cities(chat_id)
    if not cities:
        await update.effective_message.reply_text(t(lang, "no_cities"), parse_mode=ParseMode.HTML)
        return
    await update.effective_message.reply_text(
        t(lang, "remove_title"),
        reply_markup=saved_cities_keyboard(cities, action="rm"),
    )


async def remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a saved city."""
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
    city = await repo.get_city_by_id(city_id)
    if city is None or city.chat_id != chat_id:
        await query.edit_message_text(t(lang, "expired_selection"))
        return

    place = format_place(city.name, city.admin1, city.country, city.country_code)
    await repo.remove_saved_city(chat_id, city_id)
    await query.edit_message_text(
        t(lang, "city_removed", place=escape_html(place)),
        parse_mode=ParseMode.HTML,
    )


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch weather for all saved cities concurrently."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    cities = await repo.list_saved_cities(chat_id)
    if not cities:
        await update.effective_message.reply_text(t(lang, "no_cities"), parse_mode=ParseMode.HTML)
        return

    chat = await repo.get_chat(chat_id)
    units = chat.units if chat else "metric"
    client = context.application.bot_data["http_client"]

    async def _one(city: repo.CityRecord) -> str | None:
        try:
            weather = await fetch_weather(
                client, city.latitude, city.longitude, units=units
            )
            return format_weather_block(
                weather,
                name=city.name,
                admin1=city.admin1,
                country=city.country,
                country_code=city.country_code,
                lang=lang,
            )
        except WeatherError:
            logger.warning("Failed weather for city id=%s", city.id)
            return None

    results = await asyncio.gather(*[_one(c) for c in cities])
    blocks = [b for b in results if b]
    if not blocks:
        await update.effective_message.reply_text(t(lang, "api_error"))
        return

    text = format_multi_weather(blocks, lang=lang, header_key="all_title")
    # Telegram message limit is 4096; truncate gracefully if needed.
    if len(text) > 4000:
        text = text[:3990] + "…"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


def register_cities_handlers(application: Application) -> None:
    """Register city list management handlers."""
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CallbackQueryHandler(remove_callback, pattern=r"^rm:"))
