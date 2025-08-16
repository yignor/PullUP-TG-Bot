#!/usr/bin/env python3
"""
Упрощенная версия бота без pyppeteer для Railway
"""

import datetime
import os
import asyncio
import aiohttp
import re
import sys
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv
from typing import Any, cast

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения (уже настроены в Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Валидация переменных окружения для корректной типизации и раннего выхода
if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN или CHAT_ID не заданы в переменных окружения")
    sys.exit(1)

try:
    bot: Any = Bot(token=BOT_TOKEN)
    print(f"✅ Бот инициализирован успешно")
except Exception as e:
    print(f"❌ ОШИБКА при инициализации бота: {e}")
    sys.exit(1)

# URL для мониторинга
LETOBASKET_URL = "http://letobasket.ru/"

# Переменная для отслеживания уже отправленных уведомлений
sent_notifications = set()

# Паттерны для поиска команд PullUP
PULLUP_PATTERNS = [
    r'PullUP',
    r'Pull UP',
    r'PULL UP',
    r'pull up',
    r'PULLUP',
    r'pullup',
    r'Pull Up',
    r'PULL UP\s+\w+',  # PULL UP с любым словом после (например, PULL UP фарм)
    r'Pull UP\s+\w+',  # Pull UP с любым словом после
    r'pull up\s+\w+',  # pull up с любым словом после
]

players = [
    {"name": "Амбразас Никита",  "birthday": "2001-09-08"},
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

def should_check_birthdays():
    """Проверяет, нужно ли проверять дни рождения (только в 09:00)"""
    now = datetime.datetime.now()
    return now.hour == 9 and now.minute < 30

async def check_birthdays():
    """Проверяет дни рождения игроков"""
    if not should_check_birthdays():
        print("📅 Не время для проверки дней рождения (только в 09:00)")
        return
    
    print("🎂 Проверяю дни рождения...")
    
    today = datetime.datetime.now().date()
    
    for player in players:
        try:
            birthday = datetime.datetime.strptime(player["birthday"], "%Y-%m-%d").date()
            birthday_this_year = birthday.replace(year=today.year)
            
            # Если день рождения в этом году уже прошел, проверяем следующий год
            if birthday_this_year < today:
                birthday_this_year = birthday.replace(year=today.year + 1)
            
            # Если день рождения сегодня
            if birthday_this_year == today:
                age = today.year - birthday.year
                years_word = get_years_word(age)
                
                message = (
                    f"🎉 С Днем Рождения, {player['name']}! 🎉\n\n"
                    f"🎂 Сегодня тебе исполняется {age} {years_word}!\n\n"
                    f"🏀 Желаем удачи на площадке и побед! 🏆"
                )
                
                await bot.send_message(chat_id=CHAT_ID, text=message)
                print(f"✅ Отправлено поздравление {player['name']} ({age} {years_word})")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке дня рождения {player['name']}: {e}")

def find_pullup_team(text_block):
    """Ищет команду PullUP в тексте с поддержкой различных вариаций"""
    for pattern in PULLUP_PATTERNS:
        matches = re.findall(pattern, text_block, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    return None

async def parse_game_info_simple(game_url):
    """Простой парсинг информации об игре без использования браузера"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(game_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем время игры
                    time_element = soup.find('div', class_='game-time') or soup.find('span', class_='time')
                    game_time = time_element.get_text().strip() if time_element else None
                    
                    # Ищем команды
                    team1_element = soup.find('div', class_='team1') or soup.find('div', class_='left')
                    team2_element = soup.find('div', class_='team2') or soup.find('div', class_='right')
                    
                    team1 = team1_element.get_text().strip() if team1_element else "Команда 1"
                    team2 = team2_element.get_text().strip() if team2_element else "Команда 2"
                    
                    # Ищем счет
                    score_element = soup.find('div', class_='score') or soup.find('div', class_='center')
                    score = score_element.get_text().strip() if score_element else None
                    
                    return {
                        'time': game_time,
                        'team1': team1,
                        'team2': team2,
                        'score': score
                    }
    except Exception as e:
        print(f"⚠️ Ошибка при простом парсинге игры: {e}")
        return None

async def check_game_end_simple(game_url):
    """Проверяет конец игры без использования браузера"""
    try:
        game_info = await parse_game_info_simple(game_url)
        if game_info and game_info.get('score'):
            score = game_info['score']
            # Проверяем, есть ли счет в формате "NN:NN"
            if re.search(r"\d+\s*[:\-–]\s*\d+", score):
                # Создаем уникальный идентификатор для уведомления о конце
                end_notification_id = f"end_{game_url}"
                
                if end_notification_id not in sent_notifications:
                    message = (
                        f"🏁 Игра закончилась!\n\n"
                        f"🏀 {game_info.get('team1', 'Команда 1')} vs {game_info.get('team2', 'Команда 2')}\n"
                        f"📊 Счет: {score}\n\n"
                        f"Ссылка на статистику: {game_url}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    sent_notifications.add(end_notification_id)
                    print(f"✅ Отправлено уведомление о конце игры: {score}")
    except Exception as e:
        print(f"❌ Ошибка при проверке конца игры (простой метод): {e}")

async def check_letobasket_site():
    """Проверяет сайт letobasket.ru на наличие игр PullUP"""
    try:
        print(f"🔍 Проверяю сайт {LETOBASKET_URL}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(LETOBASKET_URL) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем блок между "Табло игры" и "online видеотрансляции игр доступны на странице"
                    page_text = soup.get_text(separator=' ', strip=True)
                    page_text_lower = page_text.lower()
                    
                    # Ищем начало/конец блока по нескольким вариантам, без учета регистра
                    start_variants = ["табло игры", "табло игр"]
                    end_variants = [
                        "online видеотрансляции игр доступны на странице",
                        "онлайн видеотрансляции игр доступны на странице",
                        "онлайн видеотрансляции",
                        "online видеотрансляции",
                    ]
                    start_index = -1
                    for sv in start_variants:
                        idx = page_text_lower.find(sv)
                        if idx != -1 and (start_index == -1 or idx < start_index):
                            start_index = idx
                    end_index = -1
                    for ev in end_variants:
                        idx = page_text_lower.find(ev)
                        if idx != -1 and idx > start_index:
                            if end_index == -1 or idx < end_index:
                                end_index = idx
                    
                    block_found = start_index != -1 and end_index != -1 and start_index < end_index
                    target_block = page_text[start_index:end_index] if block_found else page_text
                    if not block_found:
                        print("ℹ️ Ожидаемые маркеры не найдены, использую фолбэк: анализ всей страницы")
                    
                    # Ищем команду PullUP в найденном блоке; если не нашли, проверяем весь текст
                    pullup_team = find_pullup_team(target_block) or find_pullup_team(page_text)
                    
                    if pullup_team:
                        print(f"🏀 Найдена команда PullUP: {pullup_team}")
                        
                        # Ищем ссылку "СТРАНИЦА ИГРЫ" в HTML
                        game_links = soup.find_all('a', href=True)
                        game_page_link = None
                        
                        for link in game_links:
                            link_text = link.get_text().strip()
                            if "СТРАНИЦА ИГРЫ" in link_text or "страница игры" in link_text.lower():
                                game_page_link = link['href']
                                break
                        
                        # Если не нашли "СТРАНИЦА ИГРЫ", ищем любые похожие на страницу игры ссылки
                        if not game_page_link:
                            for link in game_links:
                                href = link['href']
                                if any(keyword in href.lower() for keyword in ['game', 'match', 'podrobno', 'id']):
                                    game_page_link = href
                                    break
                        
                        if game_page_link:
                            # Формируем полный URL
                            if game_page_link.startswith('http'):
                                full_url = game_page_link
                            else:
                                full_url = LETOBASKET_URL.rstrip('/') + '/' + game_page_link.lstrip('/')
                            
                            # Создаем уникальный идентификатор для уведомления
                            notification_id = f"pullup_{full_url}"
                            
                            # Проверяем, не отправляли ли мы уже это уведомление
                            if notification_id not in sent_notifications:
                                message = f"🏀 Найдена команда {pullup_team}!\n\n📋 СТРАНИЦА ИГРЫ: {full_url}"
                                await bot.send_message(chat_id=CHAT_ID, text=message)
                                sent_notifications.add(notification_id)
                                print(f"✅ Отправлено уведомление о команде {pullup_team}")
                                
                                # Проверяем конец игры простым методом
                                await check_game_end_simple(full_url)
                                
                            else:
                                print(f"ℹ️ Уведомление о команде {pullup_team} уже было отправлено")
                                # Проверяем конец игры
                                await check_game_end_simple(full_url)
                                    
                        else:
                            message = f"🏀 Найдена команда {pullup_team}, но ссылка на страницу игры не найдена"
                            await bot.send_message(chat_id=CHAT_ID, text=message)
                            print("⚠️ Ссылка на страницу игры не найдена")
                    else:
                        print("📊 Команды PullUP не найдены на странице")
                        
                else:
                    print(f"❌ Ошибка при загрузке сайта: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке сайта: {e}")

async def main():
    """Основная функция, выполняющая все проверки"""
    try:
        now = datetime.datetime.now()
        print(f"🤖 Запуск бота в {now.strftime('%Y-%m-%d %H:%M')}...")
        
        # Проверяем дни рождения (только в 09:00)
        await check_birthdays()
        
        # Проверяем сайт letobasket.ru
        await check_letobasket_site()

        # Тест: парсим указанную пользователем страницу статистики и отправляем уведомление, если игра окончена
        test_stats_url = (
            "http://letobasket.ru/game.html?gameId=920445&apiUrl=https://reg.infobasket.su&lang=ru#preview"
        )
        
        # Используем только простой метод без браузера
        await check_game_end_simple(test_stats_url)
        
        print("✅ Все проверки завершены")
    except Exception as e:
        print(f"❌ Критическая ошибка в main(): {e}")

if __name__ == "__main__":
    try:
        # Запускаем основную проверку (без планировщика)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        sys.exit(1)
