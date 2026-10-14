""" /start and /language handlers. """

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import Settings
from db import repository as repo
from i18n.strings import SUPPORTED_LANGUAGES, t
from services.formatter import format_weather_block
from services.weather import WeatherError, fetch_weather
from utils.helpers import ensure_chat, escape_html, get_lang
from utils.keyboards import language_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greet the user, save the chat, and send default-city weather."""
    if update.effective_chat is None or update.effective_message is None:
        return

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return

    lang = await get_lang(chat_id, context)
    settings: Settings = context.application.bot_data["settings"]
    client = context.application.bot_data["http_client"]
    chat = await repo.get_chat(chat_id)
    units = chat.units if chat else "metric"

    await update.effective_message.reply_text(
        t(lang, "welcome"),
        parse_mode=ParseMode.HTML,
        reply_markup=language_keyboard(lang),
    )

    try:
        weather = await fetch_weather(
            client,
            settings.default_city_lat,
            settings.default_city_lon,
            units=units,
        )
        block = format_weather_block(
            weather,
            name=settings.default_city_name,
            country_code="IR" if "tehran" in settings.default_city_name.lower() else None,
            lang=lang,
        )
        await update.effective_message.reply_text(block, parse_mode=ParseMode.HTML)
    except WeatherError:
        logger.exception("Failed to fetch default city weather")
        await update.effective_message.reply_text(t(lang, "api_error"))


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection keyboard."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)
    await update.effective_message.reply_text(
        t(lang, "choose_language"),
        reply_markup=language_keyboard(lang),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language button presses."""
    query = update.callback_query
    if query is None or query.data is None or update.effective_chat is None:
        return
    await query.answer()

    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return

    _, _, code = query.data.partition(":")
    if code not in SUPPORTED_LANGUAGES:
        return

    await repo.set_language(chat_id, code)
    label = SUPPORTED_LANGUAGES[code]
    await query.edit_message_text(
        t(code, "language_set", language=escape_html(label)),
        parse_mode=ParseMode.HTML,
    )


def register_start_handlers(application: Application) -> None:
    """Register /start and language handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("lang", language_command))
    application.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))
