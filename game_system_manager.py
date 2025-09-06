#!/usr/bin/env python3
"""
Единый модуль для управления системой игр PullUP
Выполняет последовательно: парсинг → создание опросов → создание анонсов
"""

import os
import asyncio
import datetime
import json
import re
from typing import Dict, List, Optional
from datetime_utils import get_moscow_time, is_today, log_current_time
from enhanced_duplicate_protection import duplicate_protection

# Переменные окружения (загружаются из системы или .env файла)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAMES_TOPIC_ID = os.getenv("GAMES_TOPIC_ID", "1282")  # Топик для опросов по играм
TARGET_TEAMS = os.getenv("TARGET_TEAMS", "PullUP,Pull Up-Фарм").split(",")

# Файлы для истории
POLLS_HISTORY_FILE = "game_polls_history.json"
ANNOUNCEMENTS_HISTORY_FILE = "game_announcements.json"

def load_polls_history() -> Dict:
    """Загружает историю созданных опросов"""
    try:
        if os.path.exists(POLLS_HISTORY_FILE):
            with open(POLLS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории опросов: {e}")
    return {}

def save_polls_history(history: Dict):
    """Сохраняет историю созданных опросов"""
    try:
        with open(POLLS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории опросов: {e}")

def load_announcements_history() -> Dict:
    """Загружает историю отправленных анонсов"""
    try:
        if os.path.exists(ANNOUNCEMENTS_HISTORY_FILE):
            with open(ANNOUNCEMENTS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"✅ Загружена история анонсов: {len(history)} записей")
                return history
        else:
            print(f"⚠️ Файл истории анонсов не найден: {ANNOUNCEMENTS_HISTORY_FILE}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории анонсов: {e}")
    print(f"📋 Возвращаем пустую историю анонсов")
    return {}

def save_announcements_history(history: Dict):
    """Сохраняет историю отправленных анонсов"""
    try:
        with open(ANNOUNCEMENTS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранена история анонсов: {len(history)} записей в {ANNOUNCEMENTS_HISTORY_FILE}")
    except Exception as e:
        print(f"⚠️ Ошибка сохранения истории анонсов: {e}")

def create_game_key(game_info: Dict) -> str:
    """Создает уникальный ключ для игры"""
    # Нормализуем время (заменяем точку на двоеточие для единообразия)
    time_str = game_info['time'].replace('.', ':')
    # Включаем время в ключ для уникальности
    return f"{game_info['date']}_{time_str}_{game_info['team1']}_{game_info['team2']}"

def create_announcement_key(game_info: Dict) -> str:
    """Создает уникальный ключ для анонса"""
    # Нормализуем время (заменяем точку на двоеточие для единообразия)
    time_str = game_info['time'].replace('.', ':')
    # Включаем время в ключ для уникальности
    return f"{game_info['date']}_{time_str}_{game_info['team1']}_{game_info['team2']}"

def get_day_of_week(date_str: str) -> str:
    """Возвращает день недели на русском языке"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y')
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return days[date_obj.weekday()]
    except:
        return ""

def get_team_category(team_name: str, opponent: str = "", game_time: str = "") -> str:
    """Определяет категорию команды по названию команды в расписании"""
    # Нормализуем название команды для сравнения
    team_upper = team_name.upper().replace(" ", "").replace("-", "").replace("_", "")
    
    # Варианты написания для состава развития (команды с "Фарм")
    development_variants = [
        "PULLUPФАРМ",
        "PULLUP-ФАРМ", 
        "PULL UPФАРМ",
        "PULL UP-ФАРМ",
        "PULL UP ФАРМ",
        "PULLUP ФАРМ"
    ]
    
    # Проверяем, является ли команда составом развития по названию
    for variant in development_variants:
        if variant in team_upper:
            return "Состав Развития"
    
    # Если команда называется просто "Pull Up" или "PullUP" (без "Фарм"), то это первый состав
    if ("PULLUP" in team_upper or "PULL UP" in team_upper) and "ФАРМ" not in team_upper:
        return "Первый состав"
    
    # Если не найден ни один вариант, то это первый состав
    return "Первый состав"

def get_team_category_with_declension(team_name: str, opponent: str = "", game_time: str = "") -> str:
    """Определяет категорию команды с правильным склонением для анонсов"""
    category = get_team_category(team_name, opponent, game_time)
    
    # Правильные склонения для анонсов
    if category == "Первый состав":
        return "Первого состава"
    elif category == "Состав Развития":
        return "состава Развития"
    else:
        return category

def determine_form_color(team1: str, team2: str) -> str:
    """Определяет цвет формы (светлая или темная)"""
    # Нормализуем названия команд для сравнения
    team1_lower = team1.lower().replace(" ", "").replace("-", "").replace("_", "")
    team2_lower = team2.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Проверяем, какая из наших команд играет
    our_team_variants = ['pullup', 'pull up', 'pullupфарм', 'pull upфарм']
    
    # Если наша команда первая - светлая форма, если вторая - темная
    for variant in our_team_variants:
        if variant in team1_lower:
            return "светлая"
        elif variant in team2_lower:
            return "темная"
    
    # По умолчанию - светлая форма
    return "светлая"

def format_date_without_year(date_str: str) -> str:
    """Форматирует дату без года (например, 27.08)"""
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        return date_obj.strftime('%d.%m')
    except:
        return date_str

class GameSystemManager:
    """Единый класс для управления всей системой игр"""
    
    def __init__(self):
        # Type annotation for bot to help linter understand it's a Telegram Bot
        self.bot: Optional['Bot'] = None
        self.polls_history = load_polls_history()
        self.announcements_history = load_announcements_history()
        
        print(f"🔍 Инициализация GameSystemManager:")
        print(f"   📊 История опросов: {len(self.polls_history)} записей")
        print(f"   📊 История анонсов: {len(self.announcements_history)} записей")
        
        if BOT_TOKEN:
            from telegram import Bot
            self.bot = Bot(token=BOT_TOKEN)
    
    def find_target_teams_in_text(self, text: str) -> List[str]:
        """Находит целевые команды в тексте"""
        found_teams = []
        # Расширенный список команд для поиска (в порядке приоритета)
        search_teams = [
            'Pull Up-Фарм',  # Сначала ищем более специфичные варианты
            'Pull Up Фарм',  # Без дефиса
            'PullUP-Фарм',   # Без пробела с дефисом
            'PullUP Фарм',   # Без пробела без дефиса
            'Pull Up',       # Обычный Pull Up
            'PullUP'         # Без пробела
        ]
        
        # Нормализуем текст для поиска
        text_normalized = text.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        for team in search_teams:
            team_normalized = team.lower().replace(" ", "").replace("-", "").replace("_", "")
            if team_normalized in text_normalized:
                found_teams.append(team)
                print(f"   ✅ Найдена команда: {team}")
        
        if not found_teams:
            print(f"   ❌ Команды Pull Up не найдены в тексте: {text[:100]}...")
            print(f"   🔍 Нормализованный текст: {text_normalized[:100]}...")
        
        return found_teams
    
    def parse_schedule_text(self, text: str) -> List[Dict]:
        """Парсит текст расписания и извлекает информацию об играх"""
        games = []
        
        # Разбиваем текст на строки
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Паттерн для игр с датой и временем
            pattern1 = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+(.+?)\s+vs\s+(.+?)\s+(.+)'
            match1 = re.search(pattern1, line)
            
            if match1:
                date, time, team1, team2, venue = match1.groups()
                games.append({
                    'date': date,
                    'time': time,
                    'team1': team1.strip(),
                    'team2': team2.strip(),
                    'venue': venue.strip(),
                    'full_text': line
                })
                continue
            
            # Паттерн для игр без времени (из табло)
            pattern2 = r'(.+?)\s+vs\s+(.+)'
            match2 = re.search(pattern2, line)
            
            if match2:
                team1, team2 = match2.groups()
                # Проверяем, есть ли наши команды
                game_text = f"{team1} {team2}"
                if self.find_target_teams_in_text(game_text):
                    games.append({
                        'date': get_moscow_time().strftime('%d.%m.%Y'),
                        'time': '20:30',  # Время по умолчанию
                        'team1': team1.strip(),
                        'team2': team2.strip(),
                        'venue': 'ВО СШОР Малый 66',  # Место по умолчанию
                        'full_text': line
                    })
        
        return games
    
    async def fetch_letobasket_schedule(self) -> List[Dict]:
        """Получает расписание игр с сайта letobasket.ru"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Получаем весь текст страницы
                        full_text = soup.get_text()
                        
                        # Ищем игры с нашими командами
                        games = []
                        
                        # Паттерн для игр в формате: дата время (место) - команда1 - команда2
                        # Поддерживаем разные форматы
                        game_patterns = [
                            r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?:\n|$)',
                            r'(\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)-(\d{2})',  # Новый формат с правильным захватом
                        ]
                        
                        # Дополнительный паттерн для строк с несколькими играми подряд
                        # Пример: "06.09.2025 12.30 (MarvelHall) - IT Basket - Pull Up-Фарм-06.09.2025 14.00 (MarvelHall) - Атомпроект - Pull Up"
                        multi_game_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2})\s+\(([^)]+)\)\s*-\s*([^-]+?)\s*-\s*([^-]+?)(?=-|\d{2}\.\d{2}\.\d{4}|$)'
                        
                        matches = []
                        for pattern in game_patterns:
                            pattern_matches = re.findall(pattern, full_text)
                            matches.extend(pattern_matches)
                        
                        # Обрабатываем паттерн для строк с несколькими играми
                        multi_game_matches = re.findall(multi_game_pattern, full_text)
                        matches.extend(multi_game_matches)
                        
                        for match in matches:
                            # Проверяем формат матча
                            if len(match) == 5:
                                if len(match[0]) == 10:  # Старый формат: полная дата
                                    date, time, venue, team1, team2 = match
                                    # Нормализуем время (заменяем точку на двоеточие)
                                    time = time.replace('.', ':')
                                else:  # Новый формат: день месяца
                                    day, venue, team1, team2, month = match
                                    
                                    # Исправляем неправильный день
                                    try:
                                        day_int = int(day)
                                        if day_int == 0:
                                            day = "30"  # Исправляем на последний день месяца
                                    except ValueError:
                                        day = "30"  # Если не можем преобразовать, используем 30
                                    
                                    # Конструируем полную дату
                                    # Получаем текущий год и месяц
                                    current_date = get_moscow_time()
                                    current_year = current_date.year
                                    current_month = current_date.month
                                    
                                    # Если день больше 28, то это может быть следующий месяц
                                    if int(day) > 28:
                                        # Проверяем, есть ли такие дни в текущем месяце
                                        import calendar
                                        days_in_current_month = calendar.monthrange(current_year, current_month)[1]
                                        if int(day) > days_in_current_month:
                                            # Переходим к следующему месяцу
                                            if current_month == 12:
                                                current_month = 1
                                                current_year += 1
                                            else:
                                                current_month += 1
                                    
                                    date = f"{day}.{current_month:02d}.{current_year}"
                                    time = "12:30"  # Время по умолчанию
                                    
                                    # Исправляем название команды, если оно было обрезано
                                    if team2.strip() == "Pull Up" and "Фарм" in str(match):
                                        team2 = "Pull Up-Фарм"
                                    elif team2.strip() == "Pull Up" and "Pull Up-Фарм" in str(match):
                                        team2 = "Pull Up-Фарм"
                                    elif team2.strip() == "Pull Up" and "Pull Up-Фарм" in str(match):
                                        team2 = "Pull Up-Фарм"
                                    
                                    # Дополнительная проверка: если в исходном тексте есть "Pull Up-Фарм", но команда обрезана
                                    if team2.strip() == "Pull Up" and "Pull Up-Фарм" in str(match):
                                        team2 = "Pull Up-Фарм"
                            else:
                                continue  # Пропускаем неправильные форматы
                            
                            game_text = f"{team1} {team2}"
                            
                            # Проверяем, есть ли наши команды
                            if self.find_target_teams_in_text(game_text):
                                games.append({
                                    'date': date,
                                    'time': time,
                                    'team1': team1.strip(),
                                    'team2': team2.strip(),
                                    'venue': venue.strip(),
                                    'full_text': f"{date} {time} ({venue}) - {team1.strip()} - {team2.strip()}"
                                })
                        
                        if games:
                            print(f"✅ Найдено {len(games)} игр с нашими командами")
                            return games
                        else:
                            print("⚠️ Игры с нашими командами не найдены")
                            return []
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return []
    
    def is_game_today(self, game_info: Dict) -> bool:
        """Проверяет, происходит ли игра сегодня"""
        try:
            return is_today(game_info['date'])
        except Exception as e:
            print(f"❌ Ошибка проверки даты игры: {e}")
            return False
    
    def should_create_poll(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли создать опрос для игры"""
        # Проверяем время выполнения (расширенное окно)
        if not self._is_correct_time_for_polls():
            return False
        
        # Создаем уникальный ключ для игры
        game_key = create_game_key(game_info)
        print(f"🔍 Проверяем ключ опроса: {game_key}")
        print(f"📋 История опросов содержит {len(self.polls_history)} записей")
        
        # Проверяем защиту от дублирования через Google Sheets
        duplicate_result = duplicate_protection.check_duplicate("ОПРОС_ИГРА", game_key)
        if duplicate_result.get('exists', False):
            print(f"⏭️ Опрос для игры {game_key} уже создан (защита через Google Sheets)")
            return False
        
        # Проверяем, не создавали ли мы уже опрос для этой игры (локальная история)
        if game_key in self.polls_history:
            print(f"⏭️ Опрос для игры {game_key} уже создан (локальная история)")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Найдены наши команды в игре: {', '.join(target_teams)}")
        
        # Проверяем, что игра в будущем (не создаем опросы для прошедших игр)
        game_date = None
        today = None
        try:
            game_date = datetime.datetime.strptime(game_info['date'], '%d.%m.%Y').date()
            today = get_moscow_time().date()
            
            if game_date < today:
                print(f"📅 Игра {game_info['date']} уже прошла, пропускаем")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки даты игры: {e}")
            return False  # Если не можем определить дату, не создаем опрос
        
        # Дополнительная проверка: не создаем опросы для игр, которые уже прошли по времени
        try:
            # Нормализуем время (заменяем точку на двоеточие)
            normalized_time = game_info['time'].replace('.', ':')
            game_time = datetime.datetime.strptime(normalized_time, '%H:%M').time()
            now = get_moscow_time().time()
            
            # Если игра сегодня и время уже прошло, не создаем опрос
            if game_date and today and game_date == today and game_time < now:
                print(f"⏰ Игра {game_info['date']} {game_info['time']} уже началась, пропускаем")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки времени игры: {e}")
        
        # Дополнительная проверка: не создаем опросы для игр, которые уже прошли
        try:
            # Нормализуем время (заменяем точку на двоеточие)
            normalized_time = game_info['time'].replace('.', ':')
            game_datetime = datetime.datetime.strptime(f"{game_info['date']} {normalized_time}", '%d.%m.%Y %H:%M')
            now = get_moscow_time()
            
            # Если игра уже прошла (более чем на 2 часа назад), не создаем опрос
            if game_datetime < now - datetime.timedelta(hours=2):
                print(f"⏰ Игра {game_info['date']} {game_info['time']} уже прошла, пропускаем")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки времени игры: {e}")
        
        # Жесткий список игр, для которых уже созданы опросы (обновляется вручную)
        game_key = create_game_key(game_info)
        existing_polls_keys = [
            "27.08.2025_20:30_Кудрово_Pull Up",
            "27.08.2025_21:45_Old Stars_Pull Up", 
            "30.08.2025_12:30_Тосно_Pull Up",
            "06.09.2025_12:30_MarvelHall_Pull Up-Фарм",
        ]
        
        if game_key in existing_polls_keys:
            print(f"⏭️ Опрос для игры {game_key} уже создан ранее (жесткий список)")
            return False
        
        # Дополнительная проверка: не создаем опросы для игр, которые уже прошли по дате
        try:
            game_date = datetime.datetime.strptime(game_info['date'], '%d.%m.%Y').date()
            today = get_moscow_time().date()
            
            # Если игра была вчера или раньше, не создаем опрос
            if game_date < today:
                print(f"📅 Игра {game_info['date']} уже прошла по дате, пропускаем")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки даты игры: {e}")
        
        print(f"✅ Игра {game_info['date']} подходит для создания опроса")
        return True
    
    def should_send_announcement(self, game_info: Dict) -> bool:
        """Проверяет, нужно ли отправить анонс для игры"""
        # Проверяем время выполнения (расширенное окно)
        if not self._is_correct_time_for_announcements():
            return False
        
        # Создаем уникальный ключ для игры
        announcement_key = create_announcement_key(game_info)
        print(f"🔍 Проверяем ключ анонса: {announcement_key}")
        print(f"📋 История анонсов содержит {len(self.announcements_history)} записей")
        
        # Проверяем защиту от дублирования через Google Sheets
        duplicate_result = duplicate_protection.check_duplicate("АНОНС_ИГРА", announcement_key)
        if duplicate_result.get('exists', False):
            print(f"⏭️ Анонс для игры {announcement_key} уже отправлен (защита через Google Sheets)")
            return False
        
        # Проверяем, не отправляли ли мы уже анонс для этой игры (локальная история)
        if announcement_key in self.announcements_history:
            print(f"⏭️ Анонс для игры {announcement_key} уже отправлен (локальная история)")
            return False
        
        # Проверяем, происходит ли игра сегодня
        if not self.is_game_today(game_info):
            print(f"📅 Игра {game_info['date']} не сегодня")
            return False
        
        # Проверяем, есть ли наши команды в игре
        game_text = f"{game_info.get('team1', '')} {game_info.get('team2', '')}"
        target_teams = self.find_target_teams_in_text(game_text)
        
        if not target_teams:
            print(f"ℹ️ Игра без наших команд: {game_info.get('team1', '')} vs {game_info.get('team2', '')}")
            return False
        
        print(f"✅ Найдены наши команды в игре: {', '.join(target_teams)}")
        print(f"✅ Игра {game_info['date']} подходит для анонса (сегодня)")
        return True
    
    def _is_correct_time_for_polls(self) -> bool:
        """Проверяет, подходящее ли время для создания опросов"""
        now = get_moscow_time()
        
        # Создаем опросы в течение всего дня (защита от дублирования через Google Sheets)
        print(f"🕐 Время подходящее для создания опросов: {now.strftime('%H:%M')} (весь день)")
        return True
    
    def _is_correct_time_for_announcements(self) -> bool:
        """Проверяет, подходящее ли время для отправки анонсов"""
        now = get_moscow_time()
        
        # Отправляем анонсы в течение всего дня (защита от дублирования через Google Sheets)
        print(f"🕐 Время подходящее для отправки анонсов: {now.strftime('%H:%M')} (весь день)")
        return True
    

    
    async def create_game_poll(self, game_info: Dict) -> bool:
        """Создает опрос для игры в топике 1282"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Определяем нашу команду и соперника
            team1 = game_info.get('team1', '')
            team2 = game_info.get('team2', '')
            
            # Находим нашу команду (используем расширенный поиск)
            our_team = None
            opponent = None
            
            # Список всех возможных названий наших команд
            our_team_variants = [
                'Pull Up-Фарм',
                'Pull Up Фарм', 
                'PullUP-Фарм',
                'PullUP Фарм',
                'Pull Up',
                'PullUP'
            ]
            
            # Нормализуем названия команд для сравнения
            team1_normalized = team1.lower().replace(" ", "").replace("-", "").replace("_", "")
            team2_normalized = team2.lower().replace(" ", "").replace("-", "").replace("_", "")
            
            for variant in our_team_variants:
                variant_normalized = variant.lower().replace(" ", "").replace("-", "").replace("_", "")
                if variant_normalized in team1_normalized:
                    our_team = team1
                    opponent = team2
                    break
                elif variant_normalized in team2_normalized:
                    our_team = team2
                    opponent = team1
                    break
            
            if not our_team:
                print(f"❌ Не удалось определить нашу команду в игре")
                return False
            
            # Определяем категорию команды
            team_category = get_team_category(our_team, opponent or "")
            day_of_week = get_day_of_week(game_info['date'])
            
            # Определяем цвет формы
            form_color = determine_form_color(game_info['team1'], game_info['team2'])
            
            # Форматируем дату без года
            date_short = format_date_without_year(game_info['date'])
            
            # Формируем вопрос в новом формате
            question = f"Летняя лига, {team_category}, {day_of_week}, против {opponent}, {date_short}, {game_info['time']}, {form_color} форма, {game_info['venue']}"
            
            # Варианты ответов с эмодзи
            options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            # Отправляем опрос (с проверкой топика)
            try:
                if GAMES_TOPIC_ID:
                    message_thread_id = int(GAMES_TOPIC_ID)
                    poll_message = await self.bot.send_poll(
                        chat_id=int(CHAT_ID),
                        question=question,
                        options=options,
                        is_anonymous=False,
                        allows_multiple_answers=False,
                        message_thread_id=message_thread_id
                    )
                else:
                    poll_message = await self.bot.send_poll(
                        chat_id=int(CHAT_ID),
                        question=question,
                        options=options,
                        is_anonymous=False,
                        allows_multiple_answers=False
                    )
            except Exception as e:
                if "Message thread not found" in str(e):
                    print(f"⚠️ Топик {GAMES_TOPIC_ID} не найден, отправляем в основной чат")
                    poll_message = await self.bot.send_poll(
                        chat_id=int(CHAT_ID),
                        question=question,
                        options=options,
                        is_anonymous=False,
                        allows_multiple_answers=False
                    )
                else:
                    raise e
            
            # Сохраняем информацию об опросе
            poll_info = {
                'message_id': poll_message.message_id,
                'poll_id': poll_message.poll.id,
                'question': question,
                'options': options,
                'game_info': game_info,
                'our_team': our_team,
                'opponent': opponent,
                'team_category': team_category,
                'day_of_week': day_of_week,
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': GAMES_TOPIC_ID
            }
            
            # Сохраняем в историю (для обратной совместимости)
            game_key = create_game_key(game_info)
            self.polls_history[game_key] = poll_info
            save_polls_history(self.polls_history)
            
            # Добавляем запись в сервисный лист для защиты от дублирования
            additional_info = f"{game_info['date']} {game_info['time']} vs {opponent} в {game_info['venue']}"
            duplicate_protection.add_record(
                "ОПРОС_ИГРА",
                game_key,
                "АКТИВЕН",
                additional_info
            )
            
            print(f"✅ Опрос для игры создан в топике {GAMES_TOPIC_ID}")
            print(f"📊 ID опроса: {poll_info['poll_id']}")
            print(f"📊 ID сообщения: {poll_info['message_id']}")
            print(f"🏀 Формат: {question}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time']}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"👥 Категория: {team_category}")
            print(f"👥 Наша команда: {our_team}")
            print(f"👥 Соперник: {opponent}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса для игры: {e}")
            return False
    
    async def find_game_link(self, team1: str, team2: str) -> Optional[tuple]:
        """Ищет ссылку на игру по командам в табло"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = "http://letobasket.ru/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем все ссылки "СТРАНИЦА ИГРЫ"
                        game_links = []
                        for link in soup.find_all('a', href=True):
                            if "СТРАНИЦА ИГРЫ" in link.get_text():
                                game_links.append(link['href'])
                        
                        print(f"🔗 Найдено ссылок: {len(game_links)}")
                        
                        # Парсим каждую ссылку и ищем Pull Up в iframe
                        for i, game_link in enumerate(game_links, 1):
                            print(f"🎮 Проверяем ссылку {i}: {game_link}")
                            
                            # Извлекаем gameId из ссылки
                            if 'gameId=' in game_link:
                                game_id = game_link.split('gameId=')[1].split('&')[0]
                                print(f"   🔍 GameId: {game_id}")
                                
                                # Формируем URL iframe
                                iframe_url = f"http://ig.russiabasket.ru/online/?id={game_id}&compId=62953&db=reg&tab=0&tv=0&color=5&logo=0&foul=0&white=1&timer24=0&blank=6&short=1&teamA=&teamB="
                                
                                try:
                                    # Загружаем iframe
                                    async with session.get(iframe_url) as iframe_response:
                                        if iframe_response.status == 200:
                                            iframe_content = await iframe_response.text()
                                            
                                            # Ищем команды в iframe
                                            iframe_text = iframe_content.upper()
                                            team1_upper = team1.upper()
                                            team2_upper = team2.upper()
                                            
                                            print(f"   🔍 Ищем команды: {team1_upper} vs {team2_upper}")
                                            print(f"   📄 Длина iframe: {len(iframe_content)} символов")
                                            
                                            # Проверяем разные варианты написания команд
                                            team1_found = (team1_upper in iframe_text or 
                                                          team1_upper.replace(' ', '') in iframe_text or
                                                          team1_upper.replace('-', ' ') in iframe_text or
                                                          team1_upper.replace(' ', '-') in iframe_text)
                                            team2_found = (team2_upper in iframe_text or 
                                                          team2_upper.replace(' ', '') in iframe_text or
                                                          team2_upper.replace('-', ' ') in iframe_text or
                                                          team2_upper.replace(' ', '-') in iframe_text)
                                            
                                            # Специальная проверка для Pull Up (включаем и обычный, и фарм)
                                            if team2_upper == 'PULL UP':
                                                # Ищем Pull Up (обычный или фарм)
                                                if 'PULL UP-ФАРМ' in iframe_text or 'PULL UP ФАРМ' in iframe_text:
                                                    team2_found = True
                                                    print(f"   ✅ Найден Pull Up-Фарм")
                                                elif 'PULL UP' in iframe_text:
                                                    team2_found = True
                                                    print(f"   ✅ Найден Pull Up (обычный)")
                                                else:
                                                    team2_found = False
                                            
                                            print(f"   🏀 {team1_upper} найдена: {'✅' if team1_found else '❌'}")
                                            print(f"   🏀 {team2_upper} найдена: {'✅' if team2_found else '❌'}")
                                            
                                            # Показываем часть iframe для отладки
                                            if 'PULL UP' in iframe_text:
                                                pull_up_pos = iframe_text.find('PULL UP')
                                                start = max(0, pull_up_pos - 50)
                                                end = min(len(iframe_text), pull_up_pos + 100)
                                                context = iframe_text[start:end]
                                                print(f"   📄 Контекст Pull Up: {context}")
                                            
                                            # Проверяем, что найдены ОБЕ команды из искомой игры
                                            if team1_found and team2_found:
                                                print(f"✅ Найдена игра {team1} vs {team2} в ссылке {i}")
                                                
                                                # Дополнительная проверка: убеждаемся, что это именно наша игра
                                                # Ищем заголовок игры в iframe
                                                title_match = re.search(r'<TITLE>.*?([^-]+)\s*-\s*([^-]+)', iframe_content, re.IGNORECASE)
                                                if title_match:
                                                    iframe_team1 = title_match.group(1).strip()
                                                    iframe_team2 = title_match.group(2).strip()
                                                    print(f"   📋 Заголовок iframe: {iframe_team1} - {iframe_team2}")
                                                    
                                                    # Проверяем, что команды в заголовке соответствуют искомым
                                                    iframe_team1_upper = iframe_team1.upper()
                                                    iframe_team2_upper = iframe_team2.upper()
                                                    
                                                    # Нормализуем названия команд для сравнения
                                                    def normalize_team_name(name):
                                                        return name.upper().replace(' ', '').replace('-', '').replace('_', '')
                                                    
                                                    team1_normalized = normalize_team_name(team1)
                                                    team2_normalized = normalize_team_name(team2)
                                                    iframe_team1_normalized = normalize_team_name(iframe_team1)
                                                    iframe_team2_normalized = normalize_team_name(iframe_team2)
                                                    
                                                    # Проверяем соответствие команд
                                                    teams_match = (
                                                        (team1_normalized in iframe_team1_normalized and team2_normalized in iframe_team2_normalized) or
                                                        (team1_normalized in iframe_team2_normalized and team2_normalized in iframe_team1_normalized)
                                                    )
                                                    
                                                    if not teams_match:
                                                        print(f"   ❌ Команды в заголовке не соответствуют искомым: {team1} vs {team2} != {iframe_team1} vs {iframe_team2}")
                                                        continue
                                                    else:
                                                        print(f"   ✅ Команды в заголовке соответствуют искомым")
                                                else:
                                                    print(f"   ⚠️ Заголовок не найден, но команды найдены в тексте")
                                                
                                                # Определяем найденную команду Pull Up
                                                found_pull_up_team = None
                                                if 'PULL UP-ФАРМ' in iframe_text:
                                                    found_pull_up_team = 'Pull Up-Фарм'
                                                elif 'PULL UP ФАРМ' in iframe_text:
                                                    found_pull_up_team = 'Pull Up Фарм'
                                                elif 'PULL UP' in iframe_text:
                                                    found_pull_up_team = 'Pull Up'
                                                
                                                print(f"   🏷️ Найдена команда в iframe: {found_pull_up_team}")
                                                
                                                # Проверяем, что это сегодняшняя игра
                                                # Ищем дату в iframe
                                                # Различные паттерны дат
                                                date_patterns = [
                                                    r'(\d{2}\.\d{2}\.\d{4})',  # DD.MM.YYYY
                                                    r'(\d{2}/\d{2}/\d{4})',    # DD/MM/YYYY
                                                    r'(\d{4}-\d{2}-\d{2})',    # YYYY-MM-DD
                                                ]
                                                
                                                dates = []
                                                for pattern in date_patterns:
                                                    found_dates = re.findall(pattern, iframe_content)
                                                    dates.extend(found_dates)
                                                
                                                # Также ищем дату в заголовке
                                                title_match = re.search(r'<TITLE>.*?(\d{2}\.\d{2}\.\d{4})', iframe_content, re.IGNORECASE)
                                                if title_match:
                                                    dates.append(title_match.group(1))
                                                
                                                if dates:
                                                    print(f"   📅 Даты в iframe: {dates}")
                                                    today_found = False
                                                    for date in dates:
                                                        if self.is_game_today({'date': date}):
                                                            today_found = True
                                                            print(f"   ✅ Сегодняшняя дата найдена: {date}")
                                                            break
                                                    
                                                    if today_found:
                                                        print(f"🔗 Ссылка для сегодняшней игры: {game_link}")
                                                        return game_link, found_pull_up_team
                                                    else:
                                                        print(f"   ⏭️ Игра не сегодня, пропускаем")
                                                else:
                                                    print(f"   ⚠️ Даты не найдены в iframe, но команды найдены - возвращаем ссылку")
                                                    print(f"🔗 Ссылка для игры: {game_link}")
                                                    return game_link, found_pull_up_team
                                            
                                        else:
                                            print(f"   ❌ Ошибка загрузки iframe: {iframe_response.status}")
                                            
                                except Exception as e:
                                    print(f"   ❌ Ошибка парсинга iframe: {e}")
                        
                        print(f"⚠️ Игра {team1} vs {team2} не найдена в табло")
                        return None
                        
                    else:
                        print(f"❌ Ошибка получения страницы: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Ошибка поиска ссылки на игру: {e}")
            return None
    
    def format_announcement_message(self, game_info: Dict, game_link: Optional[str] = None, found_team: Optional[str] = None) -> str:
        """Форматирует сообщение анонса игры"""
        # Определяем нашу команду и соперника
        team1 = game_info.get('team1', '')
        team2 = game_info.get('team2', '')
        
        print(f"🔍 Анализируем команды: {team1} vs {team2}")
        
        # Находим нашу команду (используем расширенный поиск)
        our_team = None
        opponent = None
        
        # Проверяем team1
        if any(target_team in team1 for target_team in ['Pull Up', 'PullUP']):
            our_team = team1
            opponent = team2
            print(f"   ✅ Наша команда найдена в team1: {our_team}")
            print(f"   🏀 Соперник: {opponent}")
        # Проверяем team2
        elif any(target_team in team2 for target_team in ['Pull Up', 'PullUP']):
            our_team = team2
            opponent = team1
            print(f"   ✅ Наша команда найдена в team2: {our_team}")
            print(f"   🏀 Соперник: {opponent}")
        else:
            print(f"   ❌ Наша команда не найдена ни в одной из команд")
            return f"🏀 Сегодня игра против {team2} в {game_info['venue']}.\n🕐 Время игры: {game_info['time']}."
        
        # Определяем категорию команды с правильным склонением
        # Используем найденную команду из iframe, если она передана, но всегда учитываем соперника
        if found_team:
            team_category = get_team_category_with_declension(found_team, opponent)
            print(f"🏷️ Используем найденную команду для категории: {found_team} vs {opponent} -> {team_category}")
        else:
            team_category = get_team_category_with_declension(our_team, opponent)
            print(f"🏷️ Используем команду из расписания для категории: {our_team} vs {opponent} -> {team_category}")
        
        # Формируем анонс с правильными склонениями и отдельной строкой для места
        # Нормализуем время (заменяем точку на двоеточие для ясности)
        normalized_time = game_info['time'].replace('.', ':')
        announcement = f"🏀 Сегодня игра {team_category} против {opponent}.\n"
        announcement += f"📍 Место проведения: {game_info['venue']}\n"
        announcement += f"🕐 Время игры: {normalized_time}"
        
        if game_link:
            if game_link.startswith('game.html?'):
                full_url = f"http://letobasket.ru/{game_link}"
            else:
                full_url = game_link
            announcement += f"\n🔗 Ссылка на игру: <a href=\"{full_url}\">тут</a>"
        
        return announcement
    
    async def send_game_announcement(self, game_info: Dict, game_position: int = 1, game_link: Optional[str] = None, found_team: Optional[str] = None) -> bool:
        """Отправляет анонс игры в основной топик"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Если game_link не передан, ищем ссылку на игру по командам
            if game_link is None:
                team1 = game_info.get('team1', '')
                team2 = game_info.get('team2', '')
                result = await self.find_game_link(team1, team2)
                
                # Обрабатываем результат (может быть tuple или None)
                if isinstance(result, tuple):
                    game_link, found_team = result
                else:
                    game_link, found_team = result, None
            
            # Формируем сообщение анонса
            announcement_text = self.format_announcement_message(game_info, game_link, found_team)
            
            # Мониторинг результатов будет запущен автоматически за 5 минут до игры через отдельный workflow
            if game_link:
                print(f"🎮 Мониторинг результатов будет запущен автоматически за 5 минут до игры")
            
            # Отправляем сообщение в основной топик (без указания топика)
            message = await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=announcement_text,
                parse_mode='HTML'
            )
            
            # Сохраняем информацию об анонсе
            announcement_key = create_announcement_key(game_info)
            announcement_info = {
                'message_id': message.message_id,
                'text': announcement_text,
                'game_info': game_info,
                'game_link': game_link,
                'game_position': game_position,
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': 'main'  # Основной топик
            }
            
            # Сохраняем в историю (для обратной совместимости)
            self.announcements_history[announcement_key] = announcement_info
            save_announcements_history(self.announcements_history)
            print(f"💾 Анонс добавлен в историю с ключом: {announcement_key}")
            
            # Добавляем запись в сервисный лист для защиты от дублирования
            additional_info = f"{game_info['date']} {game_info['time']} vs {game_info.get('team2', 'соперник')} в {game_info['venue']}"
            duplicate_protection.add_record(
                "АНОНС_ИГРА",
                announcement_key,
                "ОТПРАВЛЕН",
                additional_info
            )
            
            print(f"✅ Анонс игры отправлен в основной топик")
            print(f"📊 ID сообщения: {message.message_id}")
            print(f"📅 Дата: {game_info['date']}")
            print(f"🕐 Время: {game_info['time']}")
            print(f"📍 Место: {game_info['venue']}")
            print(f"🎯 Позиция в табло: {game_position}")
            if game_link:
                print(f"🔗 Ссылка: {game_link}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки анонса игры: {e}")
            return False
    

    
    async def run_full_system(self):
        """Запускает полную систему: парсинг → опросы → анонсы"""
        try:
            print("🚀 ЗАПУСК ПОЛНОЙ СИСТЕМЫ УПРАВЛЕНИЯ ИГРАМИ")
            print("=" * 60)
            
            # Используем централизованное логирование времени
            time_info = log_current_time()
            print(f"🕐 Текущее время (Москва): {time_info['formatted_datetime']}")
            print(f"📅 День недели: {time_info['weekday_name']}")
            
            print(f"\n🔧 НАСТРОЙКИ:")
            print(f"   CHAT_ID: {CHAT_ID}")
            print(f"   GAMES_TOPIC_ID: {GAMES_TOPIC_ID}")
            print(f"   TARGET_TEAMS: {TARGET_TEAMS}")
            print(f"   История опросов: {len(self.polls_history)} записей")
            print(f"   История анонсов: {len(self.announcements_history)} записей")
            
            # ШАГ 1: Парсинг расписания
            print(f"\n📊 ШАГ 1: ПАРСИНГ РАСПИСАНИЯ")
            print("-" * 40)
            games = await self.fetch_letobasket_schedule()
            
            if not games:
                print("⚠️ Игры не найдены, завершаем работу")
                return
            
            print(f"✅ Найдено {len(games)} игр")
            for i, game in enumerate(games, 1):
                print(f"   {i}. {game['full_text']}")
            
            # ШАГ 2: Создание опросов
            print(f"\n📊 ШАГ 2: СОЗДАНИЕ ОПРОСОВ")
            print("-" * 40)
            created_polls = 0
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                if self.should_create_poll(game):
                    print(f"📊 Создаю опрос для игры...")
                    if await self.create_game_poll(game):
                        created_polls += 1
            
            print(f"✅ Создано {created_polls} опросов")
            
            # ШАГ 3: Создание анонсов
            print(f"\n📢 ШАГ 3: СОЗДАНИЕ АНОНСОВ")
            print("-" * 40)
            sent_announcements = 0
            current_date = get_moscow_time().strftime('%d.%m.%Y')
            
            for game in games:
                print(f"\n🏀 Проверка игры: {game.get('team1', '')} vs {game.get('team2', '')}")
                
                # Проверяем, что это сегодняшняя игра
                if game.get('date') != current_date:
                    print(f"📅 Игра не сегодня ({game.get('date')}), пропускаем")
                    continue
                
                if self.should_send_announcement(game):
                    print(f"📢 Отправляю анонс для игры...")
                    
                    # Проверяем, есть ли игра в табло
                    team1 = game.get('team1', '')
                    team2 = game.get('team2', '')
                    game_link_result = await self.find_game_link(team1, team2)
                    
                    if game_link_result and isinstance(game_link_result, tuple):
                        game_link, found_team = game_link_result
                        print(f"✅ Игра найдена в табло, отправляем анонс с ссылкой")
                    else:
                        game_link = None
                        found_team = None
                        print(f"⚠️ Игра не найдена в табло, отправляем анонс без ссылки")
                    
                    if await self.send_game_announcement(game, game_link=game_link, found_team=found_team):
                        sent_announcements += 1
                        print(f"✅ Анонс отправлен успешно")
                else:
                    print(f"⏭️ Анонс для этой игры уже отправлен или не требуется")
            
            # Делаем break после обработки всех сегодняшних игр
            if sent_announcements > 0:
                print(f"✅ Обработаны все игры на сегодня, завершаем работу")
            
            print(f"✅ Отправлено {sent_announcements} анонсов")
            
            # Итоги
            print(f"\n📊 ИТОГИ РАБОТЫ:")
            print(f"   📊 Создано опросов: {created_polls}")
            print(f"   📢 Отправлено анонсов: {sent_announcements}")
            print(f"   📋 Всего игр обработано: {len(games)}")
            
        except Exception as e:
            print(f"❌ Ошибка выполнения системы: {e}")

# Глобальный экземпляр
game_system_manager = GameSystemManager()

async def main():
    """Основная функция"""
    await game_system_manager.run_full_system()

if __name__ == "__main__":
    asyncio.run(main())
