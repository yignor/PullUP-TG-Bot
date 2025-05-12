import datetime
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

players = [
    {"name": "Алексей",  "birthday": "2001-05-12"},
    {"name": "Иван",     "birthday": "2000-07-20"},
    {"name": "Дмитрий",  "birthday": "2002-05-12"},
]

def get_years_word(age: int) -> str:
    if 11 <= age % 100 <= 14:
        return "лет"
    elif age % 10 == 1:
        return "год"
    elif 2 <= age % 10 <= 4:
        return "года"
    else:
        return "лет"

async def check_birthdays():
    today = datetime.datetime.now()
    today_md = today.strftime("%m-%d")
    birthday_people = []

    for p in players:
        bd = datetime.datetime.strptime(p["birthday"], "%Y-%m-%d")
        if bd.strftime("%m-%d") == today_md:
            age = today.year - bd.year
            birthday_people.append(f"{p['name']} ({age} {get_years_word(age)})")

    if birthday_people:
        text = "🎉 Сегодня день рождения у: " + ", ".join(birthday_people) + "! Поздравим! 🎂"
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("✅ Отправлено:", text)
    else:
        print("📅 Сегодня нет дней рождения.")

if __name__ == "__main__":
    asyncio.run(check_birthdays())
