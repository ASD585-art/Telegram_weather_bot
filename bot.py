import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# 🔹 ВСТАВЬ сюда свои ключи:
TELEGRAM_TOKEN = "8425189026:AAGj9BK_W1q7ydcmTjlmVIUdLsnUTcVdZmc"
OPENWEATHER_API_KEY = "22f563ba71fc046b39c57a30e6f61d73"

# 🔹 Районы Караганды (координаты)
districts = {
    "михайловка": (49.8300, 73.1650),
    "новый город": (49.8070, 73.0930),
    "юговосток": (49.7800, 73.1700),
    "сортировка": (49.8800, 73.0500),
    "майкудук": (49.9500, 73.1500),
    "федоровка": (49.9000, 73.1200),
    "пришахтинск": (49.9314, 73.0868),
}

# Логирование
logging.basicConfig(level=logging.INFO)

def start(update, context):
    update.message.reply_text(
        "👋 Привет! Я бот прогноза погоды по районам Караганды.\n\n"
        "Напиши название района:\n"
        "• Михайловка\n"
        "• Новый город\n"
        "• Юговосток\n"
        "• Сортировка\n"
        "• Майкудук\n"
        "• Федоровка\n"
        "• Пришахтинск"
    )

def get_weather(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    data = requests.get(url).json()

    if data.get("cod") != 200:
        return "⚠️ Ошибка получения данных о погоде."

    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    condition = data["weather"][0]["description"]
    wind_speed = data["wind"]["speed"]
    wind_deg = data["wind"].get("deg", 0)

    # Определяем направление ветра
    dirs = ["северный", "северо-восточный", "восточный", "юго-восточный",
            "южный", "юго-западный", "западный", "северо-западный"]
    wind_dir = dirs[int((wind_deg + 22.5) / 45) % 8]

    result = (
        f"🌡 Температура: {temp}°C (ощущается как {feels}°C)\n"
        f"☁️ Состояние: {condition.capitalize()}\n"
        f"💨 Ветер: {wind_speed} м/с, {wind_dir}\n"
    )

    return result

def weather(update, context):
    user_text = update.message.text.lower()

    if user_text in districts:
        lat, lon = districts[user_text]
        forecast = get_weather(lat, lon)
        update.message.reply_text(f"📍 Погода в районе {user_text.capitalize()}:\n\n{forecast}")
    else:
        update.message.reply_text("❌ Я не знаю такого района. Напиши один из: " + ", ".join(districts.keys()))

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, weather))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
