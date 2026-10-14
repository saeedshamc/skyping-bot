"""Tests for Open-Meteo geocoding parsing and HTTP client."""

from __future__ import annotations

import httpx
import pytest
import respx

from services.cache import geocode_cache
from services.geocoding import (
    GEOCODING_URL,
    City,
    GeocodingError,
    parse_geocoding_response,
    search_cities,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    geocode_cache.clear()
    yield
    geocode_cache.clear()


def test_parse_geocoding_response(sample_geocoding_payload):
    cities = parse_geocoding_response(sample_geocoding_payload)
    assert len(cities) == 2
    assert cities[0].id == 112931
    assert cities[0].name == "Tehran"
    assert cities[0].country_code == "IR"
    assert cities[0].latitude == pytest.approx(35.69439)


def test_parse_empty_results():
    assert parse_geocoding_response({}) == []
    assert parse_geocoding_response({"results": None}) == []


def test_parse_skips_malformed():
    payload = {
        "results": [
            {"id": 1, "name": "Ok", "latitude": 1.0, "longitude": 2.0},
            {"name": "missing coords"},
        ]
    }
    cities = parse_geocoding_response(payload)
    assert len(cities) == 1
    assert cities[0].name == "Ok"


def test_city_roundtrip_dict():
    city = City(
        id=1,
        name="Paris",
        latitude=48.85,
        longitude=2.35,
        country="France",
        country_code="FR",
        admin1="Île-de-France",
    )
    restored = City.from_dict(city.to_dict())
    assert restored == city


@pytest.mark.asyncio
@respx.mock
async def test_search_cities_http(sample_geocoding_payload):
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=sample_geocoding_payload)
    )
    async with httpx.AsyncClient() as client:
        cities = await search_cities(client, "Tehran", language="en")
    assert len(cities) == 2
    assert cities[0].name == "Tehran"


@pytest.mark.asyncio
@respx.mock
async def test_search_cities_uses_cache(sample_geocoding_payload):
    route = respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=sample_geocoding_payload)
    )
    async with httpx.AsyncClient() as client:
        first = await search_cities(client, "Tehran", language="en")
        second = await search_cities(client, "Tehran", language="en")
    assert first == second
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_search_cities_http_error():
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(500))
    async with httpx.AsyncClient() as client:
        with pytest.raises(GeocodingError):
            await search_cities(client, "Nowhere", language="en")
