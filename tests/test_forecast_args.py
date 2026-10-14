"""Tests for /forecast argument parsing."""

from __future__ import annotations

from handlers.weather import DEFAULT_FORECAST_DAYS, _parse_forecast_args


def test_forecast_args_city_only():
    days, query = _parse_forecast_args(["Tehran"])
    assert days == DEFAULT_FORECAST_DAYS
    assert query == "Tehran"


def test_forecast_args_with_days():
    days, query = _parse_forecast_args(["7", "New", "York"])
    assert days == 7
    assert query == "New York"


def test_forecast_args_clamp():
    days, query = _parse_forecast_args(["99", "Paris"])
    assert days == 7
    assert query == "Paris"


def test_forecast_args_empty():
    days, query = _parse_forecast_args(None)
    assert days == DEFAULT_FORECAST_DAYS
    assert query == ""
