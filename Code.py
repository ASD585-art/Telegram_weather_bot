from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import requests
import threading
import time

# ------------------- НАСТРОЙКИ -------------------
BOT_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"
API_KEY = "ВАШ_OPENWEATHERMAP_KEY"

# Специальные районы Караганды
SPECIAL_CITIES = ["Пришахтинск", "Михайловка", "Новый Город", "Юго-Восток"]

# Изначальный город
current_city = "Пришахтинск"

# Чат для уведомлений
chat_id_for_schedule = None

# Хранение времени дождя, для которых уведомление уже отправлено
sent_rain_alerts = set()
# -------------------------------------------------

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    try:
        data = requests.get(url).json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        wind_deg = data["wind"]["deg"]
        humidity = data["main"]["humidity"]
        rain = data.get("rain", {}).get("1h", 0)
        rain_text = f"{rain} мм" if rain > 0 else "нет"
        return (f"Погода в {city}:\n"
                f"Температура: {temp}°C\n"
                f"Описание: {desc}\n"
                f"Влажность: {humidity}%\n"
                f"Скорость ветра: {wind_speed} м/с\n"
                f"Направление ветра: {wind_deg}°\n"
                f"Дождь: {rain_text}")
    except:
        return "Не удалось получить данные о погоде."

def start(update: Update, context: CallbackContext):
    global chat_id_for_schedule
    chat_id_for_schedule = update.message.chat_id
    update.message.reply_text(f"Привет! Я погодный бот. Текущий город: {current_city}\n"
                              f"Команда /change чтобы выбрать новый город.\n"
                              f"Команда /weather чтобы узнать текущую погоду.\n"
                              f"Я буду присылать погоду в 8 утра и уведомления о дожде за 30 минут до его начала.")

def change(update: Update, context: CallbackContext):
    update.message.reply_text(
        f"Шаман говорит: выберите новый город, чтобы я присылал утреннюю погоду 🌤️\n"
        f"Поддерживаются твои районы и любые города России/Казахстана/Азии. Просто напишите название города."
    )

def set_city(update: Update, context: CallbackContext):
    global current_city
    city = update.message.text.strip()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        current_city = city
        update.message.reply_text(f"Отлично! Теперь каждый день в 8 утра я буду присылать погоду для {current_city} 🌅")
    else:
        update.message.reply_text("Город не найден, попробуйте ещё раз.")

def weather_command(update: Update, context: CallbackContext):
    update.message.reply_text(get_weather(current_city))

# Проверка дождя за 30 минут до его начала
def rain_monitor(updater: Updater):
    global sent_rain_alerts
    while True:
        if chat_id_for_schedule:
            # Получаем координаты города
            city_url = f"http://api.openweathermap.org/data/2.5/weather?q={current_city}&appid={API_KEY}"
            city_data = requests.get(city_url).json()
            lat = city_data['coord']['lat']
            lon = city_data['coord']['lon']

            # One Call API для прогноза почасового
            one_call_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,daily,alerts&appid={API_KEY}&units=metric&lang=ru"
            forecast_data = requests.get(one_call_url).json()
            now_ts = int(time.time())

            for hour in forecast_data['hourly']:
                dt = hour['dt']
                rain = hour.get('rain', {}).get('1h', 0)
                # Если дождь >0 и за 30 минут до начала
                if rain > 0 and (dt - now_ts) <= 1800 and dt not in sent_rain_alerts:
                    msg = f"В {current_city} через {int((dt - now_ts)/60)} минут ожидается дождь 🌧️ Сила дождя: {rain} мм/ч"
                    updater.bot.send_message(chat_id=chat_id_for_schedule, text=msg)
                    sent_rain_alerts.add(dt)
        time.sleep(60)

def send_daily_weather(context: CallbackContext):
    if chat_id_for_schedule:
        context.bot.send_message(chat_id=chat_id_for_schedule, text=get_weather(current_city))

def schedule_daily_weather(updater: Updater):
    def run():
        while True:
            now = time.localtime()
            if now.tm_hour == 8 and now.tm_min == 0:
                updater.job_queue.run_once(send_daily_weather, 0)
                time.sleep(60)
            time.sleep(20)
    threading.Thread(target=run, daemon=True).start()
    threading.Thread(target=rain_monitor, args=(updater,), daemon=True).start()

def main():
    global updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("change", change))
    dp.add_handler(CommandHandler("weather", weather_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, set_city))

    schedule_daily_weather(updater)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
