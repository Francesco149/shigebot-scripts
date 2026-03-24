import os
import requests
import sys

APIKEY = os.environ["OPENWEATHERMAP_API_KEY"]
city = sys.argv[1]
# country = sys.argv[2]
geolocAPI = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={APIKEY}"
geolocResponse = requests.get(geolocAPI)

jsonData = geolocResponse.json(
) if geolocResponse and geolocResponse.status_code == 200 else None

if jsonData is not None:
    for item in jsonData:
        lat = item['lat']
        lon = item['lon']
        city = item['name']
        countryCode = item['country']

    weatherAPI = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={APIKEY}&units=metric"
    weatherResponse = requests.get(weatherAPI)
    jd = weatherResponse.json(
    ) if weatherResponse and weatherResponse.status_code == 200 else None

    if jd is not None:
        for i in jd:
            weather = jd["weather"][0]["description"]
            temp = str(jd["main"]["temp"])
            humidity = jd["main"]["humidity"]
            wind = jd["wind"]["speed"]

print(f"{temp}ºC in {city} {countryCode} | {weather}, Hum: {humidity}%, Wind Speed: {wind}km/h")
