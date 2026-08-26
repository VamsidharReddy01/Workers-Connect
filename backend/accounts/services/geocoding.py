import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEOAPIFY_REVERSE_URL = 'https://api.geoapify.com/v1/geocode/reverse'
GEOAPIFY_FORWARD_URL = 'https://api.geoapify.com/v1/geocode/search'
GEOAPIFY_TIMEOUT = 5  # seconds


def _get_api_key():
    key = getattr(settings, 'GEOAPIFY_API_KEY', '') or ''
    if not key:
        logger.warning('GEOAPIFY_API_KEY is not configured.')
    return key


def reverse_geocode(latitude, longitude):
    """
    Convert latitude/longitude to a human-readable location name using Geoapify.
    Returns dict with 'location_name', 'latitude', 'longitude' or None on failure.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    try:
        lat = float(latitude)
        lon = float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            logger.warning('Invalid coordinates for reverse geocoding: lat=%s lon=%s', lat, lon)
            return None
    except (TypeError, ValueError):
        logger.warning('Non-numeric coordinates for reverse geocoding: lat=%s lon=%s', latitude, longitude)
        return None

    try:
        response = requests.get(
            GEOAPIFY_REVERSE_URL,
            params={
                'lat': lat,
                'lon': lon,
                'apiKey': api_key,
                'format': 'json',
            },
            timeout=GEOAPIFY_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])
        if not results:
            logger.info('No results from Geoapify reverse geocoding for lat=%s lon=%s', lat, lon)
            return None

        result = results[0]
        location_name = result.get('formatted', '')
        if not location_name:
            # Fallback: build from components
            parts = [
                result.get('suburb') or result.get('neighbourhood', ''),
                result.get('city') or result.get('town') or result.get('village', ''),
                result.get('state', ''),
                result.get('country', ''),
            ]
            location_name = ', '.join(p for p in parts if p)

        return {
            'location_name': location_name,
            'latitude': lat,
            'longitude': lon,
        }

    except requests.exceptions.Timeout:
        logger.error('Geoapify reverse geocoding timed out for lat=%s lon=%s', lat, lon)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error('Geoapify reverse geocoding request failed: %s', exc)
        return None
    except (KeyError, ValueError, IndexError) as exc:
        logger.error('Geoapify reverse geocoding response parsing failed: %s', exc)
        return None


def forward_geocode(location_name):
    """
    Convert a location name/address to coordinates using Geoapify.
    Returns dict with 'location_name', 'latitude', 'longitude' or None on failure.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    if not location_name or not location_name.strip():
        return None

    try:
        response = requests.get(
            GEOAPIFY_FORWARD_URL,
            params={
                'text': location_name.strip(),
                'apiKey': api_key,
                'format': 'json',
                'limit': 1,
            },
            timeout=GEOAPIFY_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])
        if not results:
            logger.info('No results from Geoapify forward geocoding for: %s', location_name)
            return None

        result = results[0]
        lat = result.get('lat')
        lon = result.get('lon')

        if lat is None or lon is None:
            logger.warning('Geoapify forward geocoding returned no coordinates for: %s', location_name)
            return None

        resolved_name = result.get('formatted', location_name.strip())

        return {
            'location_name': resolved_name,
            'latitude': round(float(lat), 6),
            'longitude': round(float(lon), 6),
        }

    except requests.exceptions.Timeout:
        logger.error('Geoapify forward geocoding timed out for: %s', location_name)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error('Geoapify forward geocoding request failed: %s', exc)
        return None
    except (KeyError, ValueError, IndexError) as exc:
        logger.error('Geoapify forward geocoding response parsing failed: %s', exc)
        return None
