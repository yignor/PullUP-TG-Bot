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
    # {"name": "Булатов Игорь",  "birthday": "2002-12-01"},
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

def should_check_birthdays():
    """Проверяет, нужно ли проверять дни рождения (только в 09:00)"""
    now = datetime.datetime.now()
    return now.hour == 9 and now.minute < 30  # Проверяем только в 09:00-09:29

def find_pullup_team(text_block):
    """Ищет команду PullUP в тексте с поддержкой различных вариаций"""
    for pattern in PULLUP_PATTERNS:
        matches = re.findall(pattern, text_block, re.IGNORECASE)
        if matches:
            # Возвращаем первое найденное совпадение
            return matches[0].strip()
    return None

async def check_birthdays():
    """Проверяет дни рождения только в 09:00"""
    try:
        if not should_check_birthdays():
            print("📅 Не время для проверки дней рождения (только в 09:00)")
            return
            
        today = datetime.datetime.now()
        today_md = today.strftime("%m-%d")
        birthday_people = []

        for p in players:
            try:
                bd = datetime.datetime.strptime(p["birthday"], "%Y-%m-%d")
                if bd.strftime("%m-%d") == today_md:
                    age = today.year - bd.year
                    birthday_people.append(f"{p['name']} ({age} {get_years_word(age)})")
            except Exception as e:
                print(f"⚠️ Ошибка при обработке дня рождения {p['name']}: {e}")
                continue

        if birthday_people:
            text = "🎉 Сегодня день рождения у " + ", ".join(birthday_people) + "! \n Поздравляем! 🎂"
            await bot.send_message(chat_id=CHAT_ID, text=text)
            print("✅ Отправлено:", text)
        else:
            print("📅 Сегодня нет дней рождения.")
    except Exception as e:
        print(f"❌ Ошибка при проверке дней рождения: {e}")

async def parse_game_info(game_url):
    """Парсит информацию о игре с страницы игры"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(game_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем время игры в элементе с классом fa-calendar
                    time_element = soup.find('i', class_='fa fa-calendar')
                    game_time = None
                    
                    if time_element:
                        # Получаем текст после иконки календаря
                        time_text = time_element.get_text().strip()
                        if time_text:
                            game_time = time_text
                        else:
                            # Ищем время в родительском элементе
                            parent = time_element.parent
                            if parent:
                                time_text = parent.get_text().strip()
                                game_time = time_text
                    
                    # Ищем названия команд
                    team1_name = None
                    team2_name = None
                    
                    # Ищем элементы с protocol.team1.TeamRegionName и protocol.team2.TeamRegionName
                    page_text = soup.get_text()
                    
                    # Ищем команды в тексте страницы
                    team_patterns = [
                        r'protocol\.team1\.TeamRegionName[:\s]*([^\n\r]+)',
                        r'protocol\.team2\.TeamRegionName[:\s]*([^\n\r]+)',
                        r'Команда 1[:\s]*([^\n\r]+)',
                        r'Команда 2[:\s]*([^\n\r]+)',
                        r'Team 1[:\s]*([^\n\r]+)',
                        r'Team 2[:\s]*([^\n\r]+)'
                    ]
                    
                    for pattern in team_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            if 'team1' in pattern or 'Команда 1' in pattern or 'Team 1' in pattern:
                                team1_name = matches[0].strip()
                            elif 'team2' in pattern or 'Команда 2' in pattern or 'Team 2' in pattern:
                                team2_name = matches[0].strip()
                    
                    # Если не нашли через протокол, ищем в заголовках или других элементах
                    if not team1_name or not team2_name:
                        # Ищем в заголовках h1, h2, h3
                        headers = soup.find_all(['h1', 'h2', 'h3'])
                        for header in headers:
                            header_text = header.get_text().strip()
                            if 'против' in header_text.lower() or 'vs' in header_text.lower():
                                # Разделяем по "против" или "vs"
                                if 'против' in header_text.lower():
                                    teams = header_text.split('против')
                                else:
                                    teams = header_text.split('vs')
                                
                                if len(teams) >= 2:
                                    team1_name = teams[0].strip()
                                    team2_name = teams[1].strip()
                                    break
                    
                    return {
                        'time': game_time,
                        'team1': team1_name,
                        'team2': team2_name
                    }
                else:
                    print(f"⚠️ Ошибка при загрузке страницы игры: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Ошибка при парсинге информации о игре: {e}")
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

async def check_game_end(game_url):
    """Проверяет, нужно ли отправить уведомление о конце игры"""
    try:
        # Сначала пробуем простой парсинг без браузера
        result = await parse_game_info_simple(game_url)
        if not result:
            # Если простой парсинг не сработал, пробуем браузер
            result = await render_game_result_with_browser(game_url)
            if not result:
                return

        # Проверяем, есть ли счет в формате "NN:NN"
        score = result.get('score') or result.get('center')
        if score:
            import re
            if re.search(r"\d+\s*[:\-–]\s*\d+", score):
                end_notification_id = f"game_end_{game_url}"
                if end_notification_id not in sent_notifications:
                    team1 = result.get('team1') or result.get('left') or 'Команда 1'
                    team2 = result.get('team2') or result.get('right') or 'Команда 2'

                    message = (
                        f"🏁 Игра закончилась!\n\n"
                        f"🏀 {team1} vs {team2}\n"
                        f"📊 Счет: {score}\n\n"
                        f"Ссылка на статистику: {game_url}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    sent_notifications.add(end_notification_id)
                    print(f"✅ Отправлено уведомление о конце игры: {score}")
    except Exception as e:
        print(f"❌ Ошибка при проверке конца игры: {e}")

async def check_game_end_simple(game_url):
    """Проверяет конец игры без использования браузера"""
    try:
        game_info = await parse_game_info_simple(game_url)
        if game_info and game_info.get('score'):
            score = game_info['score']
            # Проверяем, есть ли счет в формате "NN:NN"
            import re
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

async def render_game_result_with_browser(game_url):
    """Рендерит страницу в безголовом браузере и вытаскивает итоговый счет и команды.
    Требует pyppeteer. Импортируем внутри функции, чтобы не тянуть зависимость всегда.
    """
    browser = None
    try:
        import importlib
        pyppeteer = importlib.import_module('pyppeteer')
        launch = getattr(pyppeteer, 'launch')
        
        # Настройки для работы в контейнере Railway
        browser = await launch(
            headless=True, 
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-extensions"
            ]
        )
        
        page = await browser.newPage()
        
        # Устанавливаем таймаут и ждем загрузки
        await page.goto(game_url, {"waitUntil": "networkidle2", "timeout": 30000})

        # Ждем появления основных блоков, но не падаем, если чего-то нет
        try:
            await page.waitForSelector('div.center', {'timeout': 10000})
        except Exception:
            pass

        def get_text(selector):
            return page.evaluate('(sel) => { const el = document.querySelector(sel); return el ? el.textContent.trim() : null; }', selector)

        left = await get_text('div.left')
        center = await get_text('div.center')
        right = await get_text('div.right')

        # Heuristic: если center содержит счет формата "NN:NN" или похожее — считаем, что игра завершена
        is_finished = False
        if center:
            import re as _re
            if _re.search(r"\d+\s*[:\-–]\s*\d+", center):
                is_finished = True

        return {
            'finished': is_finished,
            'left': left,
            'center': center,
            'right': right,
        }
    except Exception as e:
        print(f"⚠️ Ошибка в рендере страницы браузером: {e}")
        return None
    finally:
        # Правильно закрываем браузер
        if browser:
            try:
                await browser.close()
            except Exception as e:
                print(f"⚠️ Ошибка при закрытии браузера: {e}")

def should_send_game_notification(game_time_str):
    """Проверяет, нужно ли отправить уведомление о игре в текущий запуск"""
    if not game_time_str:
        return False
    
    try:
        # Парсим время игры
        time_formats = [
            '%H:%M',
            '%H:%M:%S',
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M'
        ]
        
        game_datetime = None
        for fmt in time_formats:
            try:
                if ':' in game_time_str and len(game_time_str.split(':')) >= 2:
                    # Если указано только время, добавляем сегодняшнюю дату
                    if len(game_time_str.split(':')) == 2:
                        today = datetime.datetime.now().strftime('%Y-%m-%d')
                        time_str_with_date = f"{today} {game_time_str}"
                        game_datetime = datetime.datetime.strptime(time_str_with_date, '%Y-%m-%d %H:%M')
                    else:
                        game_datetime = datetime.datetime.strptime(game_time_str, fmt)
                    break
            except ValueError:
                continue
        
        if game_datetime:
            now = datetime.datetime.now()
            
            # Определяем, в какой 30-минутный интервал попадает время игры
            game_hour = game_datetime.hour
            game_minute = game_datetime.minute
            
            # Определяем интервал запуска (0-29 или 30-59)
            if game_minute < 30:
                target_hour = game_hour
                target_minute_range = (0, 29)
            else:
                target_hour = game_hour
                target_minute_range = (30, 59)
            
            # Проверяем, совпадает ли текущий запуск с нужным интервалом
            current_hour = now.hour
            current_minute = now.minute
            
            # Если время игры сегодня и в нужном интервале
            if (game_datetime.date() == now.date() and 
                current_hour == target_hour and 
                target_minute_range[0] <= current_minute <= target_minute_range[1]):
                return True
            
            # Если время игры завтра и сейчас последний запуск дня (23:30-23:59)
            if (game_datetime.date() == now.date() + datetime.timedelta(days=1) and 
                current_hour == 23 and current_minute >= 30):
                return True
                
        return False
        
    except Exception as e:
        print(f"❌ Ошибка при проверке времени уведомления: {e}")
        return False

async def check_game_start(game_info, game_url):
    """Проверяет, нужно ли отправить уведомление о начале игры"""
    try:
        if not game_info or not game_info['time']:
            return
        
        if should_send_game_notification(game_info['time']):
            # Создаем уникальный идентификатор для уведомления о начале игры
            start_notification_id = f"game_start_{game_url}"
            
            if start_notification_id not in sent_notifications:
                # Формируем сообщение
                team1 = game_info['team1'] or "Команда 1"
                team2 = game_info['team2'] or "Команда 2"
                
                message = f"🏀 Игра {team1} против {team2} начинается в {game_info['time']}!\n\nСсылка на игру: {game_url}"
                
                await bot.send_message(chat_id=CHAT_ID, text=message)
                sent_notifications.add(start_notification_id)
                print(f"✅ Отправлено уведомление о начале игры: {team1} vs {team2} в {game_info['time']}")
    except Exception as e:
        print(f"❌ Ошибка при проверке начала игры: {e}")

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
                    
                    # Ищем команду PullUP с поддержкой различных вариаций (с фолбэком на весь текст)
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
                        
                        # Если не нашли "СТРАНИЦА ИГРЫ", ищем любые ссылки, похожие на страницы игр
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
                                
                                # Парсим информацию о игре и проверяем время начала
                                game_info = await parse_game_info(full_url)
                                if game_info:
                                    print(f"📅 Время игры: {game_info['time']}")
                                    print(f"🏀 Команды: {game_info['team1']} vs {game_info['team2']}")
                                    
                                    # Проверяем, нужно ли отправить уведомление о начале
                                    await check_game_start(game_info, full_url)
                                    
                                    # Проверяем конец игры
                                    await check_game_end(full_url)
                                
                            else:
                                print(f"ℹ️ Уведомление о команде {pullup_team} уже было отправлено")
                                
                                # Даже если уведомление уже отправлено, проверяем время начала
                                game_info = await parse_game_info(full_url)
                                if game_info:
                                    await check_game_start(game_info, full_url)
                                    await check_game_end(full_url)
                                        
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

async def create_poll(question, options, is_anonymous=True, allows_multiple_answers=False, explanation=None):
    """Создает опрос в Telegram чате
    
    Args:
        question (str): Вопрос опроса
        options (list): Список вариантов ответов (2-10 вариантов)
        is_anonymous (bool): Анонимный ли опрос (по умолчанию True)
        allows_multiple_answers (bool): Можно ли выбрать несколько ответов (по умолчанию False)
        explanation (str): Объяснение к опросу (опционально)
    """
    try:
        # Проверяем количество вариантов (Telegram требует 2-10)
        if len(options) < 2:
            print("❌ Ошибка: нужно минимум 2 варианта ответа")
            return None
        if len(options) > 10:
            print("❌ Ошибка: максимум 10 вариантов ответа")
            return None
        
        # Создаем опрос
        poll = await bot.send_poll(
            chat_id=CHAT_ID,
            question=question,
            options=options,
            is_anonymous=is_anonymous,
            allows_multiple_answers=allows_multiple_answers,
            explanation=explanation
        )
        
        print(f"✅ Опрос создан успешно: {question}")
        return poll
        
    except Exception as e:
        print(f"❌ Ошибка при создании опроса: {e}")
        return None

async def create_game_prediction_poll(team1, team2, game_time=None):
    """Создает опрос для предсказания результата игры"""
    question = f"🏀 Кто победит в игре {team1} vs {team2}?"
    
    if game_time:
        question += f"\n⏰ Время: {game_time}"
    
    options = [
        f"🏆 {team1}",
        f"🏆 {team2}",
        "🤝 Ничья"
    ]
    
    explanation = "Проголосуйте за победителя игры! 🏀"
    
    return await create_poll(question, options, explanation=explanation)

async def create_birthday_poll(birthday_person):
    """Создает опрос для поздравления с днем рождения"""
    question = f"🎉 Как поздравить {birthday_person} с днем рождения?"
    
    options = [
        "🎂 Торт и свечи",
        "🏀 Баскетбольный матч",
        "🎁 Подарок",
        "🍕 Пицца",
        "🎵 Музыка"
    ]
    
    explanation = "Выберите способ поздравления! 🎉"
    
    return await create_poll(question, options, explanation=explanation)

async def create_team_motivation_poll():
    """Создает опрос для мотивации команды"""
    question = "💪 Что больше всего мотивирует команду PullUP?"
    
    options = [
        "🏆 Победы и трофеи",
        "👥 Командный дух",
        "🏀 Любовь к баскетболу",
        "💪 Физическая подготовка",
        "🎯 Цели и амбиции"
    ]
    
    explanation = "Помогите понять, что движет командой! 💪"
    
    return await create_poll(question, options, explanation=explanation)

async def create_scheduled_polls(now):
    """Создает опросы по расписанию"""
    try:
        # Опрос мотивации команды каждый понедельник в 10:00
        if now.weekday() == 0 and now.hour == 10 and now.minute < 30:
            print("📊 Создаю опрос мотивации команды...")
            await create_team_motivation_poll()
        
        # Опрос в день рождения (если есть именинники)
        if should_check_birthdays():
            today = datetime.datetime.now().date()
            birthday_people = []
            
            for player in players:
                try:
                    birthday = datetime.datetime.strptime(player["birthday"], "%Y-%m-%d").date()
                    birthday_this_year = birthday.replace(year=today.year)
                    
                    if birthday_this_year < today:
                        birthday_this_year = birthday.replace(year=today.year + 1)
                    
                    if birthday_this_year == today:
                        birthday_people.append(player['name'])
                except Exception:
                    continue
            
            if birthday_people:
                print(f"🎂 Создаю опрос для поздравления {birthday_people[0]}...")
                await create_birthday_poll(birthday_people[0])
                
    except Exception as e:
        print(f"❌ Ошибка при создании запланированных опросов: {e}")

async def main():
    """Основная функция, выполняющая все проверки"""
    try:
        now = datetime.datetime.now()
        print(f"🤖 Запуск бота в {now.strftime('%Y-%m-%d %H:%M')}...")
        
        # Проверяем дни рождения (только в 09:00)
        await check_birthdays()
        
        # Проверяем сайт letobasket.ru
        await check_letobasket_site()

        # Создаем опросы по расписанию
        await create_scheduled_polls(now)

        # Тест: парсим указанную пользователем страницу статистики и отправляем уведомление, если игра окончена
        test_stats_url = (
            "http://letobasket.ru/game.html?gameId=920445&apiUrl=https://reg.infobasket.su&lang=ru#preview"
        )
        
        # Сначала пробуем простой метод, затем браузер как fallback
        try:
            await check_game_end_simple(test_stats_url)
        except Exception as e:
            print(f"⚠️ Простой метод не сработал, пробуем браузер: {e}")
            try:
                await check_game_end(test_stats_url)
            except Exception as browser_error:
                print(f"⚠️ Браузер тоже не сработал: {browser_error}")
        
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
