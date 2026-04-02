# shigebot: v2
"""
!weather <city> — current weather via OpenWeatherMap.

Usage:
  !weather Rome
  !weather London, GB

Required env var: OPENWEATHERMAP_API_KEY
"""
import json
import os
import urllib.parse
import urllib.request

import shigebot as sb


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def main():
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        sb.say("weather: OPENWEATHERMAP_API_KEY is not configured")
        return

    if not sb.ctx.args:
        sb.say(f"Usage: {sb.ctx.prefix}weather <city>")
        return

    city = " ".join(sb.ctx.args)

    try:
        geo_url = (
            "http://api.openweathermap.org/geo/1.0/direct?"
            + urllib.parse.urlencode({"q": city, "limit": 1, "appid": api_key})
        )
        results = _fetch(geo_url)
        if not results:
            sb.say(f"Location not found: {city!r}")
            return

        item    = results[0]
        lat, lon = item["lat"], item["lon"]
        resolved, country = item["name"], item["country"]

        w_url = (
            "https://api.openweathermap.org/data/2.5/weather?"
            + urllib.parse.urlencode({
                "lat": lat, "lon": lon, "appid": api_key, "units": "metric"
            })
        )
        w = _fetch(w_url)

        desc     = w["weather"][0]["description"]
        temp     = w["main"]["temp"]
        humidity = w["main"]["humidity"]
        wind     = w["wind"]["speed"]

        sb.say(f"{temp:.1f}°C in {resolved}, {country} | {desc} | humidity {humidity}% | wind {wind} m/s")

    except Exception as exc:
        sb.say(f"weather error: {exc}")
