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

# Импортируем общие модули
from game_parser import game_parser
from notification_manager import notification_manager
from players_manager import PlayersManager

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения (уже настроены в Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Валидация переменных окружения для корректной типизации и раннего выхода
if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN или CHAT_ID не заданы в переменных окружения")
    sys.exit(1)

# Инициализируем бота как None, будет создан при необходимости
bot: Any = None

def get_bot():
    """Получает инициализированного бота"""
    global bot
    if bot is None:
        try:
            if BOT_TOKEN:
                bot = Bot(token=BOT_TOKEN)
                print(f"✅ Бот инициализирован успешно")
            else:
                print("❌ BOT_TOKEN не настроен")
                return None
        except Exception as e:
            print(f"❌ ОШИБКА при инициализации бота: {e}")
            return None
    return bot

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

# Инициализируем менеджер игроков
players_manager = PlayersManager()

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
    """Проверяет, нужно ли проверять дни рождения (только в 09:00 по Москве)"""
    # Получаем московское время
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))  # UTC+3 для Москвы
    now = datetime.datetime.now(moscow_tz)
    return now.hour == 9 and now.minute < 30  # Проверяем только в 09:00-09:29 по Москве

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
            
        # Получаем игроков с днями рождения сегодня
        birthday_players = players_manager.get_players_with_birthdays_today()
        
        if birthday_players:
            birthday_messages = []
            for player in birthday_players:
                surname = player.get('surname', '')
                nickname = player.get('nickname', '')
                telegram_id = player.get('telegram_id', '')
                first_name = player.get('name', '')
                age = player.get('age', 0)
                
                # Формируем сообщение
                if nickname and telegram_id:
                    message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
                elif nickname:
                    message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" {first_name} ({age} {get_years_word(age)})!"
                elif telegram_id:
                    message = f"🎉 Сегодня день рождения у {surname} ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
                else:
                    message = f"🎉 Сегодня день рождения у {surname} {first_name} ({age} {get_years_word(age)})!"
                
                message += "\n Поздравляем! 🎂"
                birthday_messages.append(message)
            
            # Отправляем уведомления
            current_bot = get_bot()
            if current_bot:
                for message in birthday_messages:
                    await current_bot.send_message(chat_id=CHAT_ID, text=message)
                    print("✅ Отправлено:", message[:50] + "...")
            else:
                print("❌ Не удалось отправить уведомление - бот не инициализирован")
        else:
            print("📅 Сегодня нет дней рождения.")
    except Exception as e:
        print(f"❌ Ошибка при проверке дней рождения: {e}")

async def parse_game_info(game_url):
    """Парсит информацию о игре с страницы игры"""
    return await game_parser.parse_game_info(game_url)

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
        game_info = await game_parser.parse_game_info(game_url)
        if game_info:
            # Создаем уведомление о завершении игры
            await notification_manager.send_game_end_notification(game_info, game_url)
    except Exception as e:
        print(f"❌ Ошибка при проверке конца игры: {e}")

async def check_game_end_simple(game_url):
    """Проверяет конец игры без использования браузера"""
    try:
        game_info = await game_parser.parse_game_info(game_url)
        if game_info:
            # Создаем уведомление о завершении игры
            await notification_manager.send_game_end_notification(game_info, game_url)
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
            # Используем общий менеджер уведомлений
            await notification_manager.send_game_start_notification(game_info, game_url)
    except Exception as e:
        print(f"❌ Ошибка при проверке начала игры: {e}")

async def check_letobasket_site():
    """Проверяет сайт letobasket.ru на наличие игр PullUP"""
    try:
        print(f"🔍 Проверяю сайт letobasket.ru...")
        
        # Получаем свежий контент страницы
        html_content = await game_parser.get_fresh_page_content()
        
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
                    full_url = "http://letobasket.ru/".rstrip('/') + '/' + game_page_link.lstrip('/')
                
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
                    print("⚠️ Ссылка на страницу игры не найдена")
            else:
                print("📊 Команды PullUP не найдены на странице")
                    
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
            birthday_players = players_manager.get_players_with_birthdays_today()
            
            if birthday_players:
                # Берем первого именинника для создания опроса
                first_birthday_player = birthday_players[0]
                player_name = f"{first_birthday_player.get('surname', '')} {first_birthday_player.get('name', '')}"
                print(f"🎂 Создаю опрос для поздравления {player_name}...")
                await create_birthday_poll(player_name)
                
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
