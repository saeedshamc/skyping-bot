"""Global error handler."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log unexpected errors; try to notify the user briefly."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if not isinstance(update, Update) or update.effective_message is None:
        return
    try:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again later."
        )
    except Exception:
        logger.debug("Could not send error reply", exc_info=True)
