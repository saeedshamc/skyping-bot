"""Telegram command and callback handlers."""

from telegram.ext import Application

from handlers.alerts import register_alerts_handlers
from handlers.cities import register_cities_handlers
from handlers.errors import error_handler
from handlers.inline import register_inline_handlers
from handlers.start import register_start_handlers
from handlers.subscriptions import register_subscription_handlers
from handlers.weather import register_weather_handlers


def register_all_handlers(application: Application) -> None:
    """Attach every handler module to the application."""
    register_start_handlers(application)
    register_weather_handlers(application)
    register_cities_handlers(application)
    register_subscription_handlers(application)
    register_alerts_handlers(application)
    register_inline_handlers(application)
    application.add_error_handler(error_handler)
