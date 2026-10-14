"""City search via the Open-Meteo Geocoding API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from services.cache import geocode_cache

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass(frozen=True)
class City:
    """A geocoded place from Open-Meteo."""

    id: int
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    country_code: str | None = None
    admin1: str | None = None
    timezone: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for user_data / keyboard builders."""
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "country_code": self.country_code,
            "admin1": self.admin1,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> City:
        """Rebuild a City from a dict."""
        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            country=data.get("country"),
            country_code=data.get("country_code"),
            admin1=data.get("admin1"),
            timezone=data.get("timezone"),
        )


class GeocodingError(Exception):
    """Raised when the geocoding API fails."""


class GeocodingTimeout(GeocodingError):
    """Raised when the geocoding request times out."""


def parse_geocoding_response(payload: dict[str, Any]) -> list[City]:
    """Parse an Open-Meteo geocoding JSON body into City objects."""
    results = payload.get("results") or []
    cities: list[City] = []
    for item in results:
        try:
            cities.append(
                City(
                    id=int(item["id"]),
                    name=str(item["name"]),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    country=item.get("country"),
                    country_code=item.get("country_code"),
                    admin1=item.get("admin1"),
                    timezone=item.get("timezone"),
                )
            )
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping malformed geocoding result: %s", item)
    return cities


async def _fetch_once(
    client: httpx.AsyncClient,
    query: str,
    language: str,
) -> list[City]:
    response = await client.get(
        GEOCODING_URL,
        params={
            "name": query,
            "count": 5,
            "language": language,
            "format": "json",
        },
    )
    response.raise_for_status()
    return parse_geocoding_response(response.json())


async def search_cities(
    client: httpx.AsyncClient,
    query: str,
    *,
    language: str = "en",
) -> list[City]:
    """
    Search for cities matching ``query``.

    Tries the requested language first, then falls back to English.
    Results are cached for ~24 hours.
    """
    query = query.strip()
    if not query:
        return []

    cache_key = f"{language.lower()}:{query.lower()}"
    cached = geocode_cache.get(cache_key)
    if cached is not None:
        return list(cached)

    languages = [language]
    if language.lower() != "en":
        languages.append("en")

    last_error: Exception | None = None
    for attempt in range(3):
        for lang in languages:
            try:
                cities = await _fetch_once(client, query, lang)
                if cities or lang == languages[-1]:
                    geocode_cache.set(cache_key, cities)
                    return cities
            except httpx.TimeoutException as exc:
                last_error = GeocodingTimeout(str(exc))
                logger.warning(
                    "Geocoding timeout (attempt %s, lang=%s): %s",
                    attempt + 1,
                    lang,
                    exc,
                )
            except httpx.HTTPError as exc:
                last_error = GeocodingError(str(exc))
                logger.warning(
                    "Geocoding HTTP error (attempt %s, lang=%s): %s",
                    attempt + 1,
                    lang,
                    exc,
                )
        if attempt < 2:
            import asyncio

            await asyncio.sleep(0.4 * (2**attempt))

    if isinstance(last_error, GeocodingTimeout):
        raise last_error
    raise GeocodingError(str(last_error) if last_error else "Unknown geocoding error")
