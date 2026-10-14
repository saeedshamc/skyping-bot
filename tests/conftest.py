"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_geocoding_payload() -> dict:
    return {
        "results": [
            {
                "id": 112931,
                "name": "Tehran",
                "latitude": 35.69439,
                "longitude": 51.42151,
                "country": "Iran",
                "country_code": "IR",
                "admin1": "Tehran",
                "timezone": "Asia/Tehran",
            },
            {
                "id": 112046,
                "name": "Tehran",
                "latitude": 35.7,
                "longitude": 51.4,
                "country": "Iran",
                "country_code": "IR",
                "admin1": "Tehran Province",
                "timezone": "Asia/Tehran",
            },
        ]
    }


@pytest.fixture
def sample_forecast_payload() -> dict:
    return {
        "latitude": 35.7,
        "longitude": 51.4,
        "current_units": {
            "temperature_2m": "°C",
            "wind_speed_10m": "km/h",
        },
        "current": {
            "temperature_2m": 22.5,
            "apparent_temperature": 21.0,
            "relative_humidity_2m": 40,
            "weather_code": 2,
            "wind_speed_10m": 12.3,
        },
        "daily": {
            "temperature_2m_max": [28.0],
            "temperature_2m_min": [15.0],
            "precipitation_probability_max": [30],
            "weather_code": [2],
        },
    }
