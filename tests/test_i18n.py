"""Tests for bilingual strings."""

from __future__ import annotations

from i18n.strings import SUPPORTED_LANGUAGES, t


def test_supported_languages():
    assert "en" in SUPPORTED_LANGUAGES
    assert "fa" in SUPPORTED_LANGUAGES


def test_english_and_persian_welcome_differ():
    en = t("en", "welcome")
    fa = t("fa", "welcome")
    assert "SkyPing" in en
    assert "SkyPing" in fa
    assert en != fa
    assert "خوش آمدید" in fa


def test_fallback_to_english_for_unknown_lang():
    assert t("xx", "units_invalid") == t("en", "units_invalid")


def test_format_kwargs():
    msg = t("en", "city_limit", max=10)
    assert "10" in msg
