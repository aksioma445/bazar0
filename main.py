import telebot
import json
import threading
import time
from datetime import datetime, timedelta
import requests

# Ініціалізація бота
API_TOKEN = '8168170126:AAH7vBl-QqSO_xKZGu4JzSIWWr9MyD6EJR4'
GROUP_ID = -1002385577272  # Замінити на ID вашої групи
MANAGERS = [7403450527, 6097344709, 7564785089, 7342507058]  # ID адміністраторів/менеджерів

bot = telebot.TeleBot(API_TOKEN)

# Файл для зберігання даних
DATA_FILE = "user_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Завантаження даних
user_data = load_data()

# Обробник команди /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id

    # Якщо доступ вже був наданий
    if str(user_id) in user_data:
        bot.send_photo(
            user_id,
            photo=open('image_bazar1.jpg', 'rb'),
            caption=(
                f"Ви вже отримали доступ. \n"
                f"\n"
                f"Ось ваше посилання: {user_data[str(user_id)]['invite_link']}\n"
                f"\n"
                f"Ваш безкоштоний доступ діє до 30 днів!"
            )
        )
        return

    # Створення унікального посилання
    try:
        invite_link = bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,  # Обмеження на одного користувача
            expire_date=None  # Посилання не має закінчення строку
        )

        # Збереження інформації про доступ
        user_data[str(user_id)] = {
            "invite_link": invite_link.invite_link,
            "start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "notified": False
        }
        save_data(user_data)

        # Надсилання посилання користувачеві
        bot.send_photo(
            user_id,
            photo=open('image_bazar1.jpg', 'rb'),
            caption=(
                f"Дякуємо за використання бота! \n"
                f"\n"
                f"Ось ваше посилання для доступу до групи:\n{invite_link.invite_link}\n"
                f"\n"
                f"Ваш безкоштоний доступ діє до 30 днів!"
            )
        )
    except Exception as e:
        bot.send_message(user_id, "Сталася помилка під час стврення")
        print(f"Помилка створення посилання: {e}")

# Автоматичне нагадування про закінчення строку
def check_expiration():
    current_time = datetime.now()
    user_ids = list(user_data.keys())
    for user_id in user_ids:
        info = user_data[user_id]
        end_date = datetime.strptime(info["end_date"], "%Y-%m-%d %H:%M:%S")
        if not info.get("notified") and end_date - current_time <= timedelta(seconds=1000):
            bot.send_message(int(user_id), "Ваш безкоштовний доступ закінчується. \n"
                                           "\n"
                                           "Менеджер: @Elvis_cryptofathers\n"
                                           "Напишіть менеджеру для продовження доступу.\n")
            info["notified"] = True
            save_data(user_data)
        elif end_date <= current_time:
            bot.send_message(int(user_id), "Ваш доступ завершено.")
            bot.kick_chat_member(chat_id=GROUP_ID, user_id=int(user_id))  # Видалити користувача з групи
            del user_data[user_id]  # Видалити користувача з даних
            save_data(user_data)

# Команда для менеджерів продовжувати доступ
@bot.message_handler(commands=['add'])
def add_days(message):
    if message.from_user.id not in MANAGERS:
        bot.reply_to(message, "У вас немає прав для використання цієї команди.")
        return

    try:
        _, user_id, minutes = message.text.split()
        user_id = int(user_id)
        minutes = int(minutes)

        if str(user_id) not in user_data:
            bot.reply_to(message, "Цей користувач не отримував посилання.")
            return

        user_data[str(user_id)]["end_date"] = (datetime.strptime(user_data[str(user_id)]["end_date"], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        user_data[str(user_id)]["notified"] = False
        save_data(user_data)

        bot.send_message(user_id, f"Ваш доступ було продовжено на {minutes} хвилин. Ось ваше посилання: {user_data[str(user_id)]['invite_link']}")
        bot.reply_to(message, "Доступ продовжено.")
    except ValueError:
        bot.reply_to(message, "Неправильний формат. Використовуйте: /add <user_id> <minutes>")
    except Exception as e:
        bot.reply_to(message, f"Сталася помилка: {e}")

# Запуск циклу перевірки строку дії
def background_task():
    while True:
        check_expiration()
        time.sleep(10)  # Перевіряти кожні 10 секунд для тестування

threading.Thread(target=background_task, daemon=True).start()

# Keep-Alive функція
def keep_alive():
    """Пінгує PythonAnywhere URL, щоб уникнути тайм-ауту."""
    while True:
        try:
            requests.get("https://botsfortg.pythonanywhere.com/")  # Використовуйте свій Flask-лінк
            print("Keep-Alive запит успішний")
        except Exception as e:
            print(f"Помилка Keep-Alive: {e}")
        time.sleep(600)  # Пінг кожні 10 хвилин

# Обробка bot.polling() для уникнення збоїв
def start_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Помилка в bot.polling(): {e}")
            time.sleep(5)  # Зачекайте перед перезапуском

# Запускаємо Keep-Alive у фоновій нитці
threading.Thread(target=keep_alive, daemon=True).start()

# Запуск бота
start_bot()

