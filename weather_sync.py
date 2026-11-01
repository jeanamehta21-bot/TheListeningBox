"""Sync hourly regional weather for the configured Listening Box site.

Uses Open-Meteo's free forecast API; no API key or extra package required.
Set LATITUDE and LONGITUDE in config.py to the monitoring site coordinates.
"""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import LATITUDE, LONGITUDE
from database import get_connection
from research_dashboard import init_research_tables

API = "https://api.open-meteo.com/v1/forecast"


def sync_weather():
    if LATITUDE is None or LONGITUDE is None:
        raise SystemExit(
            "Weather is not configured. Set the monitoring site's LATITUDE "
            "and LONGITUDE in config.py first."
        )
    query = urlencode({
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "auto",
    })
    request = Request(API + "?" + query, headers={"User-Agent": "TheListeningBox/1.0"})
    with urlopen(request, timeout=25) as response:
        payload = json.load(response)

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    synced_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    init_research_tables()
    inserted = 0
    with get_connection() as conn:
        for i, observed_at in enumerate(times):
            def value(key):
                values = hourly.get(key) or []
                return values[i] if i < len(values) else None
            conn.execute("""
                INSERT INTO weather_observations(
                  observed_at,temperature_c,relative_humidity,precipitation_mm,
                  wind_speed_kmh,weather_code,synced_at
                ) VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(observed_at) DO UPDATE SET
                  temperature_c=excluded.temperature_c,
                  relative_humidity=excluded.relative_humidity,
                  precipitation_mm=excluded.precipitation_mm,
                  wind_speed_kmh=excluded.wind_speed_kmh,
                  weather_code=excluded.weather_code,
                  synced_at=excluded.synced_at
            """, (observed_at, value("temperature_2m"), value("relative_humidity_2m"),
                  value("precipitation"), value("wind_speed_10m"), value("weather_code"), synced_at))
            inserted += 1
    print(f"Weather sync complete: {inserted} hourly records saved.")


if __name__ == "__main__":
    sync_weather()
