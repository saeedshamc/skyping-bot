"""Rain alert preference commands."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from config import Settings
from db import repository as repo
from i18n.strings import t
from utils.helpers import ensure_chat, get_lang, user_is_admin


def _parse_threshold(raw: str) -> int | None:
    if not raw.isdigit():
        return None
    value = int(raw)
    if 1 <= value <= 100:
        return value
    return None


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts [on|off|NN] [threshold]."""
    if update.effective_message is None:
        return
    chat_id = await ensure_chat(update, context)
    if chat_id is None:
        return
    lang = await get_lang(chat_id, context)

    if not await user_is_admin(update, context):
        await update.effective_message.reply_text(t(lang, "admin_only"))
        return

    chat = await repo.get_chat(chat_id)
    if chat is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    args = [a.lower() for a in (context.args or [])]

    if not args:
        key = "alerts_status_on" if chat.rain_alerts else "alerts_status_off"
        await update.effective_message.reply_text(
            t(lang, key, threshold=chat.rain_threshold),
            parse_mode=ParseMode.HTML,
        )
        return

    if args[0] == "off":
        await repo.set_rain_alerts(chat_id, enabled=False)
        await update.effective_message.reply_text(t(lang, "alerts_disabled"))
        return

    if args[0] == "on":
        threshold = chat.rain_threshold or settings.default_rain_threshold
        if len(args) >= 2:
            parsed = _parse_threshold(args[1])
            if parsed is None:
                await update.effective_message.reply_text(
                    t(lang, "alerts_threshold_invalid")
                )
                return
            threshold = parsed
        cities = await repo.list_saved_cities(chat_id)
        if not cities:
            await update.effective_message.reply_text(t(lang, "alerts_need_cities"))
            return
        await repo.set_rain_alerts(chat_id, enabled=True, threshold=threshold)
        await update.effective_message.reply_text(
            t(lang, "alerts_enabled", threshold=threshold),
            parse_mode=ParseMode.HTML,
        )
        return

    # `/alerts 70` — set threshold only
    parsed = _parse_threshold(args[0])
    if parsed is not None:
        await repo.set_rain_alerts(chat_id, threshold=parsed)
        if chat.rain_alerts:
            await update.effective_message.reply_text(
                t(lang, "alerts_enabled", threshold=parsed),
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.effective_message.reply_text(
                t(lang, "alerts_status_off", threshold=parsed),
                parse_mode=ParseMode.HTML,
            )
        return

    await update.effective_message.reply_text(
        t(lang, "alerts_usage"),
        parse_mode=ParseMode.HTML,
    )


def register_alerts_handlers(application: Application) -> None:
    """Register /alerts command."""
    application.add_handler(CommandHandler("alerts", alerts_command))
