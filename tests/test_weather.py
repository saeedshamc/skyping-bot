"""Tests for Open-Meteo forecast parsing and HTTP client."""

from __future__ import annotations

import httpx
import pytest
import respx

from services.cache import weather_cache
from services.weather import (
    FORECAST_URL,
    WeatherError,
    fetch_daily_forecast,
    fetch_weather,
    parse_daily_forecast_response,
    parse_forecast_response,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    weather_cache.clear()
    yield
    weather_cache.clear()


def test_parse_forecast_response(sample_forecast_payload):
    weather = parse_forecast_response(sample_forecast_payload, "metric")
    assert weather.temperature == 22.5
    assert weather.feels_like == 21.0
    assert weather.humidity == 40
    assert weather.wind_speed == 12.3
    assert weather.weather_code == 2
    assert weather.temp_min == 15.0
    assert weather.temp_max == 28.0
    assert weather.precip_probability == 30
    assert weather.temperature_unit == "°C"
    assert weather.units == "metric"


def test_parse_forecast_missing_precip(sample_forecast_payload):
    sample_forecast_payload["daily"]["precipitation_probability_max"] = [None]
    weather = parse_forecast_response(sample_forecast_payload, "metric")
    assert weather.precip_probability is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_http(sample_forecast_payload):
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=sample_forecast_payload)
    )
    async with httpx.AsyncClient() as client:
        weather = await fetch_weather(client, 35.7, 51.4, units="metric")
    assert weather.temperature == 22.5
    assert weather.weather_code == 2


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_cache(sample_forecast_payload):
    route = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=sample_forecast_payload)
    )
    async with httpx.AsyncClient() as client:
        a = await fetch_weather(client, 35.6892, 51.3890, units="metric")
        b = await fetch_weather(client, 35.6892, 51.3890, units="metric")
    assert a == b
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_http_error():
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as client:
        with pytest.raises(WeatherError):
            await fetch_weather(client, 0.0, 0.0, units="metric")


def test_parse_daily_forecast_response():
    payload = {
        "latitude": 35.7,
        "longitude": 51.4,
        "daily_units": {"temperature_2m_max": "°C"},
        "daily": {
            "time": ["2026-10-15", "2026-10-16", "2026-10-17"],
            "weather_code": [2, 61, 0],
            "temperature_2m_max": [28.0, 22.0, 30.0],
            "temperature_2m_min": [15.0, 12.0, 14.0],
            "precipitation_probability_max": [30, 80, 5],
        },
    }
    forecast = parse_daily_forecast_response(payload, "metric")
    assert len(forecast.days) == 3
    assert forecast.days[1].weather_code == 61
    assert forecast.days[1].precip_probability == 80
    assert forecast.days[0].temp_max == 28.0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_daily_forecast_http():
    payload = {
        "latitude": 35.7,
        "longitude": 51.4,
        "daily_units": {"temperature_2m_max": "°C"},
        "daily": {
            "time": ["2026-10-15", "2026-10-16"],
            "weather_code": [2, 3],
            "temperature_2m_max": [28.0, 26.0],
            "temperature_2m_min": [15.0, 14.0],
            "precipitation_probability_max": [20, 40],
        },
    }
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))
    async with httpx.AsyncClient() as client:
        forecast = await fetch_daily_forecast(
            client, 35.7, 51.4, days=2, units="metric"
        )
    assert len(forecast.days) == 2
    assert forecast.days[0].temp_min == 15.0
