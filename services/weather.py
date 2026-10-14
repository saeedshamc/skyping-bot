"""Forecast fetching from Open-Meteo."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from services.cache import weather_cache

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class Weather:
    """Parsed current + daily summary for a location."""

    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    weather_code: int
    temp_min: float
    temp_max: float
    precip_probability: int | None
    units: str  # metric | imperial
    temperature_unit: str
    wind_speed_unit: str


class WeatherError(Exception):
    """Raised when the forecast API fails."""


class WeatherTimeout(WeatherError):
    """Raised when the forecast request times out."""


def parse_forecast_response(payload: dict[str, Any], units: str) -> Weather:
    """Parse an Open-Meteo forecast JSON body into a Weather dataclass."""
    current = payload["current"]
    daily = payload["daily"]
    current_units = payload.get("current_units") or {}
    daily_units = payload.get("daily_units") or {}

    precip: int | None = None
    probs = daily.get("precipitation_probability_max")
    if probs and len(probs) > 0 and probs[0] is not None:
        precip = int(probs[0])

    return Weather(
        latitude=float(payload["latitude"]),
        longitude=float(payload["longitude"]),
        temperature=float(current["temperature_2m"]),
        feels_like=float(current["apparent_temperature"]),
        humidity=int(current["relative_humidity_2m"]),
        wind_speed=float(current["wind_speed_10m"]),
        weather_code=int(current["weather_code"]),
        temp_min=float(daily["temperature_2m_min"][0]),
        temp_max=float(daily["temperature_2m_max"][0]),
        precip_probability=precip,
        units=units,
        temperature_unit=str(current_units.get("temperature_2m", "°C")),
        wind_speed_unit=str(current_units.get("wind_speed_10m", "km/h")),
    )


def _unit_params(units: str) -> dict[str, str]:
    if units == "imperial":
        return {
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
        }
    return {
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    }


async def fetch_weather(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    *,
    units: str = "metric",
) -> Weather:
    """
    Fetch current weather + today's daily min/max for coordinates.

    Results are cached for ~10 minutes per lat/lon/units key.
    """
    units = "imperial" if units == "imperial" else "metric"
    cache_key = f"{latitude:.4f}:{longitude:.4f}:{units}"
    cached = weather_cache.get(cache_key)
    if cached is not None:
        return cached

    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "weather_code,wind_speed_10m"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "forecast_days": 1,
        "timezone": "auto",
        **_unit_params(units),
    }

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await client.get(FORECAST_URL, params=params)
            response.raise_for_status()
            weather = parse_forecast_response(response.json(), units)
            weather_cache.set(cache_key, weather)
            return weather
        except httpx.TimeoutException as exc:
            last_error = WeatherTimeout(str(exc))
            logger.warning("Weather timeout (attempt %s): %s", attempt + 1, exc)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError) as exc:
            last_error = WeatherError(str(exc))
            logger.warning("Weather error (attempt %s): %s", attempt + 1, exc)
        if attempt < 2:
            import asyncio

            await asyncio.sleep(0.4 * (2**attempt))

    if isinstance(last_error, WeatherTimeout):
        raise last_error
    raise WeatherError(str(last_error) if last_error else "Unknown weather error")
