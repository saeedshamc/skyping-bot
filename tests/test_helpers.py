"""Tests for small utility helpers."""

from __future__ import annotations

from utils.helpers import country_flag, escape_html, format_place, is_valid_time


def test_country_flag_iran():
    assert country_flag("IR") == "🇮🇷"


def test_country_flag_france():
    assert country_flag("FR") == "🇫🇷"


def test_country_flag_invalid():
    assert country_flag(None) == ""
    assert country_flag("X") == ""
    assert country_flag("12") == ""


def test_escape_html():
    assert escape_html("<b>&") == "&lt;b&gt;&amp;"


def test_format_place():
    label = format_place("Paris", "Île-de-France", "France", "FR")
    assert label == "Paris, Île-de-France, France 🇫🇷"


def test_is_valid_time():
    assert is_valid_time("07:30")
    assert is_valid_time("23:59")
    assert not is_valid_time("7:30")
    assert not is_valid_time("24:00")
    assert not is_valid_time("ab:cd")
