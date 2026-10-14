"""Tests for WMO mapping and HTML weather formatting."""

from __future__ import annotations

from services.formatter import (
    format_multi_weather,
    format_weather_block,
    wmo_to_emoji_and_text,
)
from services.weather import Weather


def _sample_weather(**overrides) -> Weather:
    data = dict(
        latitude=35.7,
        longitude=51.4,
        temperature=22.5,
        feels_like=21.0,
        humidity=40,
        wind_speed=12.3,
        weather_code=2,
        temp_min=15.0,
        temp_max=28.0,
        precip_probability=30,
        units="metric",
        temperature_unit="°C",
        wind_speed_unit="km/h",
    )
    data.update(overrides)
    return Weather(**data)


def test_wmo_clear_sky_english():
    emoji, text = wmo_to_emoji_and_text(0, "en")
    assert emoji == "☀️"
    assert text == "Clear sky"


def test_wmo_partly_cloudy_persian():
    emoji, text = wmo_to_emoji_and_text(2, "fa")
    assert emoji == "⛅"
    assert "نیمه" in text or "ابری" in text


def test_wmo_unknown_code():
    emoji, text = wmo_to_emoji_and_text(9999, "en")
    assert emoji == "🌡"
    assert text == "Unknown"


def test_format_weather_block_contains_fields():
    block = format_weather_block(
        _sample_weather(),
        name="Tehran",
        country="Iran",
        country_code="IR",
        lang="en",
    )
    assert "Tehran" in block
    assert "Iran" in block
    assert "🇮🇷" in block
    assert "22.5" in block
    assert "21.0" in block
    assert "15.0" in block
    assert "28.0" in block
    assert "12.3" in block
    assert "40%" in block
    assert "30%" in block
    assert "<b>" in block


def test_format_escapes_html_in_city_name():
    block = format_weather_block(
        _sample_weather(),
        name="<script>x</script>",
        lang="en",
    )
    assert "<script>" not in block
    assert "&lt;script&gt;" in block


def test_format_multi_weather_joins_blocks():
    w = _sample_weather()
    a = format_weather_block(w, name="A", lang="en")
    b = format_weather_block(w, name="B", lang="en")
    text = format_multi_weather([a, b], lang="en", header_key="all_title")
    assert "A" in text and "B" in text
    assert "Weather for all" in text


def test_persian_rtl_mark_present():
    block = format_weather_block(
        _sample_weather(),
        name="تهران",
        lang="fa",
    )
    assert "\u200f" in block
    assert "تهران" in block
