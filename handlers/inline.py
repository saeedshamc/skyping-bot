"""Inline query mode: @bot <city> in any chat."""

from __future__ import annotations

import logging

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, InlineQueryHandler

from i18n.strings import t
from services.formatter import format_inline_description, format_weather_block
from services.geocoding import GeocodingError, search_cities
from services.weather import WeatherError, fetch_weather
from utils.helpers import format_place

logger = logging.getLogger(__name__)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer inline city searches with current weather articles."""
    inline = update.inline_query
    if inline is None:
        return

    query = (inline.query or "").strip()
    # Prefer Telegram UI language, fall back to English.
    lang_code = (inline.from_user.language_code or "en").lower()
    lang = "fa" if lang_code.startswith("fa") else "en"

    if len(query) < 2:
        await inline.answer(
            [],
            cache_time=5,
            is_personal=True,
            switch_pm_text=t(lang, "inline_type_city")[:64],
            switch_pm_parameter="inline",
        )
        return

    client = context.application.bot_data["http_client"]

    try:
        cities = await search_cities(client, query, language=lang)
    except GeocodingError:
        logger.warning("Inline geocoding failed for %r", query)
        await inline.answer([], cache_time=10, is_personal=True)
        return

    results: list[InlineQueryResultArticle] = []
    for city in cities[:5]:
        place = format_place(city.name, city.admin1, city.country, city.country_code)
        try:
            weather = await fetch_weather(
                client,
                city.latitude,
                city.longitude,
                units="metric",
            )
        except WeatherError:
            logger.warning("Inline weather failed for %s", city.name)
            continue

        body = format_weather_block(
            weather,
            name=city.name,
            admin1=city.admin1,
            country=city.country,
            country_code=city.country_code,
            lang=lang,
        )
        results.append(
            InlineQueryResultArticle(
                id=str(city.id),
                title=place[:64],
                description=format_inline_description(weather, lang)[:120],
                input_message_content=InputTextMessageContent(
                    message_text=body,
                    parse_mode=ParseMode.HTML,
                ),
            )
        )

    await inline.answer(results, cache_time=60, is_personal=True)


def register_inline_handlers(application: Application) -> None:
    """Register inline query handler."""
    application.add_handler(InlineQueryHandler(inline_query))
