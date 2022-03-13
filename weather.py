import requests
from config import api_weather


def get_weather(city):
    try:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_weather}"
                                f"&units=metric")
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        speed = data["wind"]["speed"]
        return f"В городе {city} температура равна {temp}℃ , давление - {pressure} мм.рт.ст, влажность - {humidity}%, скорость" \
               f" ветра - {speed}м/с"
    except Exception as e:
        return "Город не найден"
