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
    {"name": "Амбразас Никита",  "birthday": "2001-09-08"},
    {"name": "Булатов Игорь",  "birthday": "2002-12-01"},
    {"name": "Валиев Равиль",  "birthday": "1998-05-21"},
    {"name": "Веселов Егор",  "birthday": "2006-12-25"},
    {"name": "Гайда Иван",     "birthday": "1984-03-28"},
    {"name": "Головченко Максим",  "birthday": "2002-06-29"},
    {"name": "Горбунов Никита",  "birthday": "2004-10-13"},
    {"name": "Гребнев Антон",  "birthday": "1990-12-24"},
    {"name": "Долгих Владислав",  "birthday": "2002-06-09"},
    {"name": "Долгих Денис",  "birthday": "1997-04-23"},
    {"name": "Дроздов Даниил",  "birthday": "1999-04-24"},
    {"name": "Дудкин Евгений",  "birthday": "2004-03-03"},
    {"name": "Звягинцев Олег",  "birthday": "1992-01-20"},
    {"name": "Касаткин Александр",     "birthday": "2006-04-19"},
    {"name": "Литус Дмитрий",  "birthday": "2005-08-04"},
    {"name": "Логинов Никита",  "birthday": "2007-10-24"},
    {"name": "Максимов Иван",  "birthday": "2001-07-24"},
    {"name": "Морецкий Игорь",  "birthday": "1986-04-30"},
    {"name": "Морозов Евгений",  "birthday": "2002-06-13"},
    {"name": "Мясников Юрий",  "birthday": "2003-05-28"},
    {"name": "Никитин Артем",  "birthday": "2000-06-30"},
    {"name": "Новиков Савва",  "birthday": "2007-01-14"},
    {"name": "Оболенский Григорий",  "birthday": "2004-11-06"},
    {"name": "Смирнов Александр",  "birthday": "2006-11-23"},
    {"name": "Сопп Эдуард",  "birthday": "2008-11-12"},
    {"name": "Федотов Дмитрий",  "birthday": "2003-09-04"},
    {"name": "Харитонов Эдуард",  "birthday": "2005-06-16"},
    {"name": "Чжан Тимофей",  "birthday": "2005-03-28"},
    {"name": "Шараев Юрий",  "birthday": "1987-09-20"},
    {"name": "Шахманов Максим",  "birthday": "2006-08-17"},
    {"name": "Ясинко Денис",  "birthday": "1987-06-18"},
    {"name": "Якупов Данил",  "birthday": "2005-06-02"},
    {"name": "Хан Александр",  "birthday": "1994-08-24"},
#    {"name": "НЕ ПИЗДАБОЛ МАКСИМ СЕРГЕЕВИЧ",  "birthday": "7777-77-77"}
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
        text = "🎉 Сегодня день рождения у " + ", ".join(birthday_people) + "! \n Поздравляем! 🎂"
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("✅ Отправлено:", text)
    else:
        print("📅 Сегодня нет дней рождения.")

if __name__ == "__main__":
    asyncio.run(check_birthdays())
