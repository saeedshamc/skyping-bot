"""HTML weather message builders and WMO code mapping."""

from __future__ import annotations

from datetime import date, datetime

from services.weather import DailyForecast, Weather
from i18n.strings import t
from utils.helpers import escape_html, format_place


# WMO weather interpretation codes -> (emoji, i18n key suffix)
WMO_MAP: dict[int, tuple[str, str]] = {
    0: ("☀️", "wmo_0"),
    1: ("🌤", "wmo_1"),
    2: ("⛅", "wmo_2"),
    3: ("☁️", "wmo_3"),
    45: ("🌫", "wmo_45"),
    48: ("🌫", "wmo_48"),
    51: ("🌦", "wmo_51"),
    53: ("🌦", "wmo_53"),
    55: ("🌧", "wmo_55"),
    56: ("🌧", "wmo_56"),
    57: ("🌧", "wmo_57"),
    61: ("🌧", "wmo_61"),
    63: ("🌧", "wmo_63"),
    65: ("⛈", "wmo_65"),
    66: ("🌧", "wmo_66"),
    67: ("🌧", "wmo_67"),
    71: ("🌨", "wmo_71"),
    73: ("🌨", "wmo_73"),
    75: ("❄️", "wmo_75"),
    77: ("🌨", "wmo_77"),
    80: ("🌦", "wmo_80"),
    81: ("🌧", "wmo_81"),
    82: ("⛈", "wmo_82"),
    85: ("🌨", "wmo_85"),
    86: ("❄️", "wmo_86"),
    95: ("⛈", "wmo_95"),
    96: ("⛈", "wmo_96"),
    99: ("⛈", "wmo_99"),
}


def wmo_to_emoji_and_text(code: int, lang: str = "en") -> tuple[str, str]:
    """Map a WMO weather_code to (emoji, localized description)."""
    entry = WMO_MAP.get(code)
    if entry is None:
        return "🌡", t(lang, "wmo_unknown")
    emoji, key = entry
    return emoji, t(lang, key)


def format_weather_block(
    weather: Weather,
    *,
    name: str,
    admin1: str | None = None,
    country: str | None = None,
    country_code: str | None = None,
    lang: str = "en",
) -> str:
    """Build one HTML weather block for a city."""
    place = format_place(name, admin1, country, country_code)
    emoji, condition = wmo_to_emoji_and_text(weather.weather_code, lang)
    tu = weather.temperature_unit
    wu = weather.wind_speed_unit

    precip_line = ""
    if weather.precip_probability is not None:
        precip_line = (
            f"💧 <b>{escape_html(t(lang, 'precip'))}:</b> "
            f"{weather.precip_probability}%\n"
        )

    # RTL mark helps mixed Persian/Latin layouts stay readable.
    rtl = "\u200f" if lang == "fa" else ""

    return (
        f"{rtl}{t(lang, 'weather_header', place=escape_html(place))}\n"
        f"{emoji} <b>{escape_html(t(lang, 'condition'))}:</b> {escape_html(condition)}\n"
        f"🌡 <b>{escape_html(t(lang, 'temperature'))}:</b> "
        f"{weather.temperature:.1f}{escape_html(tu)}\n"
        f"🤚 <b>{escape_html(t(lang, 'feels_like'))}:</b> "
        f"{weather.feels_like:.1f}{escape_html(tu)}\n"
        f"⬇️⬆️ <b>{escape_html(t(lang, 'today_range'))}:</b> "
        f"{weather.temp_min:.1f} / {weather.temp_max:.1f}{escape_html(tu)}\n"
        f"💨 <b>{escape_html(t(lang, 'wind'))}:</b> "
        f"{weather.wind_speed:.1f} {escape_html(wu)}\n"
        f"💦 <b>{escape_html(t(lang, 'humidity'))}:</b> {weather.humidity}%\n"
        f"{precip_line}"
    ).rstrip()


def format_multi_weather(
    blocks: list[str],
    *,
    lang: str = "en",
    header_key: str | None = "all_title",
) -> str:
    """Join several weather blocks into one message."""
    parts: list[str] = []
    if header_key:
        parts.append(t(lang, header_key))
    parts.extend(blocks)
    return "\n\n".join(parts)


def _format_forecast_date(iso_date: str, lang: str) -> str:
    """Human-friendly day label for a YYYY-MM-DD date."""
    try:
        d = date.fromisoformat(iso_date)
    except ValueError:
        return iso_date
    today = datetime.now().date()
    delta = (d - today).days
    if delta == 0:
        return t(lang, "day_today")
    if delta == 1:
        return t(lang, "day_tomorrow")
    weekday_keys = (
        "weekday_mon",
        "weekday_tue",
        "weekday_wed",
        "weekday_thu",
        "weekday_fri",
        "weekday_sat",
        "weekday_sun",
    )
    return f"{t(lang, weekday_keys[d.weekday()])} {d.strftime('%m/%d')}"


def format_daily_forecast(
    forecast: DailyForecast,
    *,
    name: str,
    admin1: str | None = None,
    country: str | None = None,
    country_code: str | None = None,
    lang: str = "en",
) -> str:
    """Build an HTML multi-day forecast message."""
    place = format_place(name, admin1, country, country_code)
    rtl = "\u200f" if lang == "fa" else ""
    tu = forecast.temperature_unit
    lines = [
        f"{rtl}{t(lang, 'forecast_header', place=escape_html(place), days=len(forecast.days))}",
        "",
    ]
    for day in forecast.days:
        emoji, condition = wmo_to_emoji_and_text(day.weather_code, lang)
        label = _format_forecast_date(day.date, lang)
        precip = (
            f" · 💧{day.precip_probability}%"
            if day.precip_probability is not None
            else ""
        )
        lines.append(
            f"{emoji} <b>{escape_html(label)}</b>: "
            f"{day.temp_min:.0f}/{day.temp_max:.0f}{escape_html(tu)} — "
            f"{escape_html(condition)}{precip}"
        )
    return "\n".join(lines)


def format_rain_alert(
    *,
    place: str,
    precip_probability: int,
    threshold: int,
    lang: str = "en",
) -> str:
    """Build a short rain-alert notification."""
    rtl = "\u200f" if lang == "fa" else ""
    return (
        f"{rtl}{t(lang, 'rain_alert_header')}\n"
        f"📍 <b>{escape_html(place)}</b>\n"
        f"💧 {escape_html(t(lang, 'precip'))}: <b>{precip_probability}%</b>\n"
        f"{t(lang, 'rain_alert_threshold', threshold=threshold)}"
    )


def format_inline_description(weather: Weather, lang: str = "en") -> str:
    """Short one-line description for inline query results."""
    emoji, condition = wmo_to_emoji_and_text(weather.weather_code, lang)
    return (
        f"{emoji} {weather.temperature:.0f}{weather.temperature_unit} · {condition}"
    )
