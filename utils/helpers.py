"""Flag emoji, HTML escaping, admin checks, and small helpers."""

from __future__ import annotations

import logging
import re
from html import escape as html_escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Chat, Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def escape_html(text: str | None) -> str:
    """Escape text for Telegram HTML parse mode."""
    if text is None:
        return ""
    return html_escape(str(text), quote=False)


def country_flag(country_code: str | None) -> str:
    """Convert an ISO 3166-1 alpha-2 code to a flag emoji."""
    if not country_code or len(country_code) != 2:
        return ""
    code = country_code.upper()
    if not code.isalpha():
        return ""
    return "".join(chr(ord(c) - ord("A") + 0x1F1E6) for c in code)


def format_place(
    name: str,
    admin1: str | None = None,
    country: str | None = None,
    country_code: str | None = None,
) -> str:
    """Build a human-readable place label with optional flag."""
    parts = [name]
    if admin1:
        parts.append(admin1)
    if country:
        parts.append(country)
    label = ", ".join(parts)
    flag = country_flag(country_code)
    if flag:
        label = f"{label} {flag}"
    return label


def is_valid_time(value: str) -> bool:
    """Return True if value looks like HH:MM in 24-hour format."""
    return bool(_TIME_RE.match(value.strip()))


async def ensure_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    """Ensure the chat exists in the DB; return chat_id or None."""
    from config import Settings
    from db import repository as repo

    chat = update.effective_chat
    if chat is None:
        return None
    settings: Settings = context.application.bot_data["settings"]
    await repo.upsert_chat(
        chat.id,
        chat.type,
        timezone=settings.default_timezone,
        send_time=settings.default_send_time,
        language=settings.default_language,
    )
    return chat.id


async def get_lang(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Resolve UI language for a chat."""
    from db import repository as repo

    chat = await repo.get_chat(chat_id)
    if chat and chat.language:
        return chat.language
    settings = context.application.bot_data["settings"]
    return settings.default_language


async def user_is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """
    Return True if the acting user may change group subscriptions.

    Private chats always allow. In groups/supergroups, the user must be
    an administrator (or creator). Channels are not command-driven.
    """
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return False
    if chat.type == "private":
        return True
    if chat.type not in ("group", "supergroup"):
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except Exception:
        logger.exception("Failed to check admin status for chat %s", chat.id)
        return False
    return member.status in ("administrator", "creator")


def chat_label(chat: Chat) -> str:
    """Short debug label for a chat."""
    return f"{chat.type}:{chat.id}"
