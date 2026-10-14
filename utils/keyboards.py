"""Inline keyboard builders."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from i18n.strings import SUPPORTED_LANGUAGES
from utils.helpers import format_place


def city_search_keyboard(
    cities: list[dict],
    *,
    action: str = "wx",
) -> InlineKeyboardMarkup:
    """
    Build a keyboard for geocoding search results.

    Each button callback is ``{action}:{geoname_id}`` (short payload).
    ``cities`` items need keys: id, name, admin1, country, country_code.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for city in cities:
        label = format_place(
            city["name"],
            city.get("admin1"),
            city.get("country"),
            city.get("country_code"),
        )
        if len(label) > 64:
            label = label[:61] + "…"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{action}:{city['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def saved_cities_keyboard(
    cities: list,
    *,
    action: str,
) -> InlineKeyboardMarkup:
    """Keyboard for saved cities (list / remove / unsubscribe)."""
    rows: list[list[InlineKeyboardButton]] = []
    for city in cities:
        label = format_place(
            city.name, city.admin1, city.country, city.country_code
        )
        if len(label) > 64:
            label = label[:61] + "…"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{action}:{city.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def language_keyboard(current: str | None = None) -> InlineKeyboardMarkup:
    """Keyboard to pick UI language."""
    rows: list[list[InlineKeyboardButton]] = []
    for code, label in SUPPORTED_LANGUAGES.items():
        prefix = "✓ " if code == current else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"lang:{code}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)
