import re
import requests
from config import WEATHER_API_KEY


def extract_city(query):
    match = re.search(r"weather\s+(?:in|at)?\s*(.+)", query.lower())

    if match:
        return match.group(1).strip().title()

    return query.strip().title()


def get_weather(query):

    city = extract_city(query)

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)

    print(response.url)

    if response.status_code != 200:
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return "Couldn't fetch weather."

    data = response.json()

    country = data["sys"]["country"]
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    weather = data["weather"][0]["description"]

    return (
        f"Weather in {city}, {country}\n"
        f"Temperature: {temperature}°C\n"
        f"Feels Like: {feels_like}°C\n"
        f"Humidity: {humidity}%\n"
        f"Condition: {weather}"
    )