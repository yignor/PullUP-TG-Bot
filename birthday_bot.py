import datetime
import os
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# Список игроков с датами рождения:
players = [
    {"name": "Алексей",  "birthday": "1990-05-12"},
    {"name": "Иван",     "birthday": "2000-07-20"},
    {"name": "Дмитрий",  "birthday": "2002-05-12"},
    # Добавь своих игроков сюда...
]

def get_years_word(age: int) -> str:
    """Склонение слова 'год' по-русски."""
    if 11 <= age % 100 <= 14:
        return "лет"
    elif age % 10 == 1:
        return "год"
    elif 2 <= age % 10 <= 4:
        return "года"
    else:
        return "лет"

def check_birthdays():
    today = datetime.datetime.now()
    today_md = today.strftime("%m-%d")
    birthday_people = []

    for player in players:
        # Преобразуем строку в дату
        birth_date = datetime.datetime.strptime(player["birthday"], "%Y-%m-%d")
        if birth_date.strftime("%m-%d") == today_md:
            age = today.year - birth_date.year
            word = get_years_word(age)
            birthday_people.append(f"{player['name']} ({age} {word})")

    if birthday_people:
        names_list = ", ".join(birthday_people)
        message = f"🎉 Сегодня день рождения у: {names_list}! Поздравим! 🎂"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print("✅ Отправлено:", message)
    else:
        print("📅 Сегодня дней рождения нет.")

if __name__ == "__main__":
    check_birthdays()
