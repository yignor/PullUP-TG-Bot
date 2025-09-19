#!/usr/bin/env python3
"""
Улучшенный модуль для работы с опросами тренировок
Создание опросов, сбор данных и сохранение в Google Sheets
"""

import os
import asyncio
import datetime
import json
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters
import gspread
from datetime_utils import get_moscow_time, log_current_time
from google.oauth2.service_account import Credentials
from enhanced_duplicate_protection import duplicate_protection

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Настройки Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]



def get_current_week_period():
    """Возвращает период текущей недели (понедельник-воскресенье)"""
    now = get_moscow_time()
    
    # Находим понедельник текущей недели
    days_back = now.weekday()  # 0 = понедельник, 6 = воскресенье
    current_monday = now - datetime.timedelta(days=days_back)
    
    # Воскресенье = понедельник + 6 дней
    current_sunday = current_monday + datetime.timedelta(days=6)
    
    return current_monday.date(), current_sunday.date()

def get_next_week_period():
    """Возвращает период следующей недели (понедельник-воскресенье)"""
    now = get_moscow_time()
    
    # Находим следующий понедельник
    days_ahead = 0 - now.weekday()  # 0 = понедельник
    if days_ahead <= 0:  # Если сегодня понедельник или позже
        days_ahead += 7
    next_monday = now + datetime.timedelta(days=days_ahead)
    
    # Воскресенье = понедельник + 6 дней
    next_sunday = next_monday + datetime.timedelta(days=6)
    
    return next_monday.date(), next_sunday.date()

class TrainingPollsManager:
    """Управление опросами тренировок"""
    
    def __init__(self):
        self.bot = None
        self.gc = None
        self.spreadsheet = None
        self.current_poll_info = {}
        self.poll_results = {}
        self._init_bot()
        self._init_google_sheets()
    
    def _init_bot(self):
        """Инициализация бота"""
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Бот инициализирован")
        else:
            print("❌ BOT_TOKEN не настроен")
    
    def _init_google_sheets(self):
        """Инициализация Google Sheets"""
        try:
            # Сначала пробуем загрузить из отдельного JSON файла
            if os.path.exists('google_credentials.json'):
                with open('google_credentials.json', 'r', encoding='utf-8') as f:
                    creds_dict = json.load(f)
                print("✅ Google credentials загружены из google_credentials.json")
            elif GOOGLE_SHEETS_CREDENTIALS:
                creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
                print("✅ Google credentials загружены из переменной окружения")
            else:
                print("⚠️ GOOGLE_SHEETS_CREDENTIALS не настроен")
                return
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
            self.gc = gspread.authorize(creds)
            
            if SPREADSHEET_ID:
                self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
                print("✅ Google Sheets подключен успешно")
            else:
                print("⚠️ SPREADSHEET_ID не настроен")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Sheets: {e}")
    
    async def create_weekly_training_poll(self):
        """Создает еженедельный опрос тренировок"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            # Получаем период текущей недели (для которой создается опрос)
            week_start, week_end = get_current_week_period()
            
            # Получаем даты тренировок
            tuesday_date = self.get_next_tuesday_date()
            thursday_date = self.get_next_thursday_date()
            friday_date = self.get_next_friday_date()
            
            # Определяем места тренировок для недели
            locations = self.get_training_locations(week_start)
            
            # Формируем вопрос с датами тренировок
            question = f"Тренировки {tuesday_date.strftime('%d.%m')}, {thursday_date.strftime('%d.%m')} и {friday_date.strftime('%d.%m')}"
            
            # Формируем упрощенные варианты ответов
            options = [
                "Вторник, 21:30, зал Динамо (Крестовский остров)",
                "Четверг, 21:30, зал Динамо (Игровая тренировка, максимум 9 человек)",
                "Пятница, 20:30, зал СШОР ВО",
                "Тренер",
                "Нет"
            ]
            
            # Отправляем опрос
            message_thread_id = int(ANNOUNCEMENTS_TOPIC_ID) if ANNOUNCEMENTS_TOPIC_ID else None
            
            if not CHAT_ID:
                print("❌ CHAT_ID не настроен")
                return False
            
            poll_message = await self.bot.send_poll(
                chat_id=int(CHAT_ID),
                question=question,
                options=options,
                is_anonymous=False,
                allows_multiple_answers=True,
                message_thread_id=message_thread_id
            )
            
            # Сохраняем информацию об опросе
            self.current_poll_info = {
                'message_id': poll_message.message_id,
                'poll_id': poll_message.poll.id,
                'question': question,
                'options': options,
                'date': self.get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': ANNOUNCEMENTS_TOPIC_ID,
                'tuesday_date': tuesday_date.isoformat(),
                'thursday_date': thursday_date.isoformat(),
                'friday_date': friday_date.isoformat(),
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'tuesday_location': {'time': '21:30', 'location': 'зал Динамо (Крестовский остров)'},
                'thursday_location': {'time': '21:30', 'location': 'зал Динамо (Игровая тренировка, максимум 9 человек)'},
                'friday_location': {'time': '20:30', 'location': 'зал СШОР ВО'}
            }
            
            # Сохраняем в файл (для обратной совместимости)
            with open('current_poll_info.json', 'w', encoding='utf-8') as f:
                json.dump(self.current_poll_info, f, ensure_ascii=False, indent=2)
            
            # Добавляем запись в сервисный лист для защиты от дублирования
            additional_info = f"Вторник {tuesday_date.strftime('%d.%m')}, Четверг {thursday_date.strftime('%d.%m')}, Пятница {friday_date.strftime('%d.%m')}"
            duplicate_protection.add_record(
                "ОПРОС_ТРЕНИРОВКА",
                str(poll_message.poll.id),
                "АКТИВЕН",
                additional_info
            )
            
            # Создаем структуру в Google Sheets
            try:
                print(f"📊 Создание структуры в Google Sheets...")
                self._create_training_structure(tuesday_date, friday_date, str(poll_message.poll.id))
                print(f"✅ Структура в Google Sheets создана")
            except Exception as e:
                print(f"⚠️ Ошибка создания структуры в Google Sheets: {e}")
            
            print(f"✅ Опрос создан успешно")
            print(f"📊 ID опроса: {self.current_poll_info['poll_id']}")
            print(f"📊 ID сообщения: {self.current_poll_info['message_id']}")
            print(f"📅 Период недели: {week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}")
            print(f"📅 Вторник: {tuesday_date.strftime('%d.%m.%Y')} 21:30 зал Динамо (Крестовский остров)")
            print(f"📅 Пятница: {friday_date.strftime('%d.%m.%Y')} 20:30 зал СШОР ВО")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса: {e}")
            return False
    
    def should_create_weekly_poll(self):
        """Проверяет, нужно ли создавать еженедельный опрос"""
        now = self.get_moscow_time()
        
        # Создаем опрос каждое воскресенье в 10:00-23:59
        if now.weekday() == 6 and now.hour >= 10:
            # Проверяем, не был ли уже создан опрос сегодня
            if self._was_poll_created_today():
                print("📊 Опрос уже был создан сегодня")
                return False
            return True
        
        return False
    
    def _was_poll_created_today(self) -> bool:
        """Проверяет, был ли уже создан опрос сегодня (усиленная защита)"""
        try:
            # Используем новую систему защиты от дублирования
            today = self.get_moscow_time().date()
            today_str = today.strftime('%d.%m.%Y')
            
            # Получаем активные опросы тренировок за сегодня
            training_polls = duplicate_protection.get_records_by_type("ОПРОС_ТРЕНИРОВКА")
            
            for poll in training_polls:
                if poll.get('date', '').startswith(today_str) and poll.get('status') == 'АКТИВЕН':
                    print(f"📊 Опрос уже создан сегодня: {poll.get('date')}")
                    return True
            
            # Для обратной совместимости проверяем старый файл
            if os.path.exists('current_poll_info.json'):
                try:
                    with open('current_poll_info.json', 'r', encoding='utf-8') as f:
                        poll_info = json.load(f)
                    
                    poll_date_str = poll_info.get('date', '')
                    if poll_date_str:
                        poll_date = datetime.datetime.fromisoformat(poll_date_str.replace('Z', '+00:00'))
                        poll_date_moscow = poll_date.replace(tzinfo=datetime.timezone.utc).astimezone(
                            datetime.timezone(datetime.timedelta(hours=3))
                        )
                        
                        if poll_date_moscow.date() == today:
                            print(f"📊 Опрос уже создан сегодня (старый файл): {poll_date_moscow.strftime('%Y-%m-%d %H:%M')}")
                            return True
                except Exception as e:
                    print(f"⚠️ Ошибка чтения старого файла: {e}")
            
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка проверки даты создания опроса: {e}")
            return False
    
    def should_collect_tuesday_data(self):
        """Проверяет, нужно ли собирать данные за вторник"""
        now = self.get_moscow_time()
        
        # Собираем данные каждую среду в 10:00-23:59
        if now.weekday() == 2 and now.hour >= 10:
            # Проверяем, не были ли уже собраны данные сегодня
            if self._was_data_collected_today("Вторник"):
                print("📊 Данные за вторник уже были собраны сегодня")
                return False
            
            # Проверяем, существует ли опрос для сбора данных
            if not self._poll_exists():
                print("❌ Опрос не найден - невозможно собрать данные")
                return False
            
            return True
        
        return False
    
    def should_collect_friday_data(self):
        """Проверяет, нужно ли собирать данные за пятницу"""
        now = self.get_moscow_time()
        
        # Собираем данные каждую субботу в 10:00-23:59
        if now.weekday() == 5 and now.hour >= 10:
            # Проверяем, не были ли уже собраны данные сегодня
            if self._was_data_collected_today("Пятница"):
                print("📊 Данные за пятницу уже были собраны сегодня")
                return False
            
            # Проверяем, существует ли опрос для сбора данных
            if not self._poll_exists():
                print("❌ Опрос не найден - невозможно собрать данные")
                return False
            
            return True
        
        return False
    
    def _was_data_collected_today(self, day_name: str) -> bool:
        """Проверяет, были ли уже собраны данные за указанный день сегодня"""
        try:
            # Проверяем файл с результатами сбора данных
            if not os.path.exists('training_data_collection_log.json'):
                print(f"📄 Файл training_data_collection_log.json не найден")
                return False
            
            # Проверяем размер файла
            file_size = os.path.getsize('training_data_collection_log.json')
            if file_size == 0:
                print(f"📄 Файл training_data_collection_log.json пустой")
                return False
            
            with open('training_data_collection_log.json', 'r', encoding='utf-8') as f:
                collection_log = json.load(f)
            
            today = self.get_moscow_time().date().isoformat()
            
            # Проверяем, есть ли запись о сборе данных за сегодня
            for entry in collection_log.get('collections', []):
                if (entry.get('date') == today and 
                    entry.get('day_name') == day_name):
                    print(f"📊 Данные за {day_name} уже собраны сегодня: {entry.get('time', '')}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка проверки сбора данных: {e}")
            return False
    
    def _log_data_collection(self, day_name: str):
        """Логирует сбор данных"""
        try:
            # Загружаем существующий лог или создаем новый
            if os.path.exists('training_data_collection_log.json'):
                with open('training_data_collection_log.json', 'r', encoding='utf-8') as f:
                    collection_log = json.load(f)
            else:
                collection_log = {'collections': []}
            
            # Добавляем новую запись
            now = self.get_moscow_time()
            new_entry = {
                'date': now.date().isoformat(),
                'time': now.strftime('%H:%M:%S'),
                'day_name': day_name,
                'timestamp': now.isoformat()
            }
            
            collection_log['collections'].append(new_entry)
            
            # Сохраняем лог
            with open('training_data_collection_log.json', 'w', encoding='utf-8') as f:
                json.dump(collection_log, f, ensure_ascii=False, indent=2)
            
            print(f"📝 Сбор данных за {day_name} залогирован")
            
        except Exception as e:
            print(f"⚠️ Ошибка логирования сбора данных: {e}")
    
    def find_player_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Ищет игрока по Telegram ID в листе 'Игроки'"""
        if not self.spreadsheet:
            return None
        
        try:
            worksheet = self.spreadsheet.worksheet("Игроки")
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:
                return None
            
            headers = all_values[0]
            
            # Ищем колонку с Telegram ID
            telegram_id_col = None
            for i, header in enumerate(headers):
                if 'telegram' in header.lower() or 'id' in header.lower():
                    telegram_id_col = i
                    break
            
            if telegram_id_col is None:
                return None
            
            # Ищем игрока
            for row in all_values[1:]:
                if len(row) > telegram_id_col:
                    cell_value = row[telegram_id_col].strip()
                    
                    if (cell_value == telegram_id or 
                        cell_value == f"@{telegram_id}" or 
                        cell_value == f"@{telegram_id.replace('@', '')}" or
                        cell_value == telegram_id.replace('@', '')):
                        
                        return {
                            'data': row,
                            'headers': headers
                        }
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска игрока: {e}")
            return None
    
    def get_player_full_name(self, player_data: Dict) -> Tuple[str, str]:
        """Получает фамилию и имя игрока"""
        if not player_data:
            return "Неизвестный", "игрок"
        
        headers = player_data['headers']
        data = player_data['data']
        
        # Ищем колонки с фамилией и именем
        surname_col = None
        name_col = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'фамилия' in header_lower:
                surname_col = i
            elif 'имя' in header_lower:
                name_col = i
        
        # Получаем фамилию и имя
        surname = ""
        name = ""
        
        if surname_col is not None and len(data) > surname_col:
            surname = data[surname_col].strip()
        
        if name_col is not None and len(data) > name_col:
            name = data[name_col].strip()
        
        return surname, name

    def format_player_name(self, user_name: str, telegram_id: str) -> str:
        """Форматирует имя игрока с учетом данных из таблицы"""
        # Убираем @ из telegram_id для поиска
        clean_telegram_id = telegram_id.replace('@', '')
        
        # Ищем игрока в таблице
        player_data = self.find_player_by_telegram_id(clean_telegram_id)
        
        if player_data:
            surname, name = self.get_player_full_name(player_data)
            if surname and name:
                return f"{surname} {name}"
        
        # Если не найден, возвращаем имя и telegram_id
        return f"{user_name} ({telegram_id})"
    
    def _get_or_create_training_worksheet(self):
        """Получает или создает лист 'Тренировки'"""
        if not self.spreadsheet:
            print("❌ Google Sheets не подключен")
            return None
            
        try:
            worksheet = self.spreadsheet.worksheet("Тренировки")
            print("✅ Лист 'Тренировки' найден")
            return worksheet
        except gspread.WorksheetNotFound:
            # Создаем новый лист с заголовками
            worksheet = self.spreadsheet.add_worksheet(title="Тренировки", rows=1000, cols=10)
            print("✅ Лист 'Тренировки' создан")
            
            # Добавляем заголовки (упрощенная структура)
            headers = [
                "Дата", 
                "ID", 
                "Фамилия", 
                "Имя", 
                "Telegram ID"
            ]
            worksheet.append_row(headers)
            
            # Форматируем заголовки
            worksheet.format('A1:E1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            return worksheet

    def _check_existing_poll(self, tuesday_date: datetime.date, friday_date: datetime.date) -> bool:
        """Проверяет, существует ли уже опрос для указанных дат тренировок"""
        try:
            worksheet = self._get_or_create_training_worksheet()
            if not worksheet:
                print("❌ Не удалось получить лист 'Тренировки'")
                return False
                
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:  # Только заголовки
                return False
            
            # Ищем существующие опросы с теми же датами тренировок
            for row in all_values[1:]:
                if len(row) >= 3:  # Проверяем, что есть достаточно колонок
                    poll_date_str = row[0]  # Дата опроса
                    training_date_str = row[2]  # Дата тренировки
                    
                    # Пропускаем строки, которые не содержат дату
                    if not training_date_str or not training_date_str.strip():
                        continue
                    
                    # Проверяем, что это действительно дата (содержит точки или дефисы)
                    if not ('.' in training_date_str or '-' in training_date_str):
                        continue
                    
                    try:
                        # Парсим дату тренировки
                        if '.' in training_date_str:
                            training_date = datetime.datetime.strptime(training_date_str, '%d.%m.%Y').date()
                        else:
                            training_date = datetime.datetime.strptime(training_date_str, '%Y-%m-%d').date()
                        
                        # Проверяем, совпадает ли дата с нашими тренировками
                        if training_date in [tuesday_date, friday_date]:
                            print(f"✅ Найден существующий опрос для даты {training_date_str}")
                            return True
                    except Exception as e:
                        # Пропускаем строки, которые не являются датами
                        continue
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка проверки существующих опросов: {e}")
            return False

    def get_next_tuesday_date(self):
        """Возвращает дату следующего вторника"""
        now = self.get_moscow_time()
        days_ahead = 1 - now.weekday()  # 1 = вторник
        if days_ahead <= 0:  # Если сегодня вторник или позже
            days_ahead += 7
        next_tuesday = now + datetime.timedelta(days=days_ahead)
        return next_tuesday.date()
    
    def get_next_thursday_date(self):
        """Возвращает дату следующего четверга"""
        now = self.get_moscow_time()
        days_ahead = 3 - now.weekday()  # 3 = четверг
        if days_ahead <= 0:  # Если сегодня четверг или позже
            days_ahead += 7
        next_thursday = now + datetime.timedelta(days=days_ahead)
        return next_thursday.date()
    
    def get_next_friday_date(self):
        """Возвращает дату следующей пятницы"""
        now = self.get_moscow_time()
        days_ahead = 4 - now.weekday()  # 4 = пятница
        if days_ahead <= 0:  # Если сегодня пятница или позже
            days_ahead += 7
        next_friday = now + datetime.timedelta(days=days_ahead)
        return next_friday.date()
    
    def get_training_locations(self, week_start_date):
        """Определяет места тренировок для недели"""
        # Единая система тренировок: Динамо + СШОР ВО
        return {
            'tuesday': {'time': '21:30', 'location': 'зал Динамо (Крестовский остров)'},
            'friday': {'time': '20:30', 'location': 'зал СШОР ВО'}
        }
    
    def get_moscow_time(self):
        """Получает текущее время в московском часовом поясе"""
        return get_moscow_time()

    def _create_training_structure(self, tuesday_date: datetime.date, friday_date: datetime.date, poll_id: str):
        """Создает структуру данных в листе 'Тренировки'"""
        try:
            worksheet = self._get_or_create_training_worksheet()
            if not worksheet:
                print("❌ Не удалось получить лист 'Тренировки'")
                return
            
            # Получаем текущую дату создания опроса
            now = self.get_moscow_time()
            poll_creation_date = now.strftime('%d.%m.%Y')
            
            # Создаем основную строку опроса
            main_row_data = [
                poll_creation_date,  # Дата создания опроса
                poll_id,             # ID опроса
                "",                  # Фамилия (пустая)
                "",                  # Имя (пустая)
                ""                   # Telegram ID (пустой)
            ]
            worksheet.append_row(main_row_data)
            
            # Создаем строку для вторника
            tuesday_header = [
                tuesday_date.strftime('%d.%m.%Y'),  # Дата вторника с годом
                "Вторник",                       # ID содержит день недели
                "",                              # Фамилия (пустая)
                "",                              # Имя (пустая)
                ""                               # Telegram ID (пустой)
            ]
            worksheet.append_row(tuesday_header)
            
            # Создаем строку для пятницы
            friday_header = [
                friday_date.strftime('%d.%m.%Y'),   # Дата пятницы с годом
                "Пятница",                       # ID содержит день недели
                "",                              # Фамилия (пустая)
                "",                              # Имя (пустая)
                ""                               # Telegram ID (пустой)
            ]
            worksheet.append_row(friday_header)
            
            print(f"✅ Структура данных создана в листе 'Тренировки'")
            
        except Exception as e:
            print(f"❌ Ошибка создания структуры данных: {e}")

    async def collect_poll_data(self, target_day: str):
        """Собирает данные опроса за указанный день"""
        if not self.bot:
            print("❌ Бот не инициализирован")
            return False
        
        # Получаем информацию об опросе из Google Sheets
        if not self.spreadsheet:
            print("❌ Google Sheets не подключен")
            return False
        
        try:
            worksheet = self.spreadsheet.worksheet("Тренировки")
        except gspread.WorksheetNotFound:
            print("❌ Лист 'Тренировки' не найден")
            return False
        
        all_values = worksheet.get_all_values()
        
        if len(all_values) <= 1:
            print("📄 Лист 'Тренировки' пустой")
            return False
        
        # Ищем активные опросы
        active_polls = []
        for i, row in enumerate(all_values):
            if len(row) > 1 and row[1] and len(row[1]) > 10 and row[1] not in ["Вторник", "Пятница"]:
                active_polls.append({
                    'poll_id': row[1],
                    'date': row[0],
                    'row': i + 1
                })
        
        if not active_polls:
            print("❌ Активные опросы не найдены в Google Sheets")
            return False
            
        # Берем последний опрос
        latest_poll = active_polls[-1]
        poll_info = {
            'poll_id': latest_poll['poll_id'],
            'date': latest_poll['date']
        }
        
        print(f"📊 Сбор данных за {target_day}")
        print(f"📊 ID опроса: {poll_info['poll_id']}")
        print(f"📊 Дата опроса: {poll_info['date']}")
        
        # Проверяем, что бот инициализирован
        if not self.bot:
            print("❌ Бот не инициализирован")
            return False
            
        # Получаем результаты опроса через API
        try:
            # Получаем информацию об опросе
            if CHAT_ID:
                poll_info_api = await self.bot.get_chat(chat_id=int(CHAT_ID))
                print(f"📊 Получена информация о чате: {poll_info_api.id}")
            
            # Получаем обновления от бота с большим лимитом и offset
            all_updates = []
            offset = 0
            limit = 100
            
            # Получаем обновления порциями
            for attempt in range(10):  # Увеличиваем до 10 попыток
                try:
                    updates_batch = await self.bot.get_updates(limit=limit, offset=offset, timeout=10)
                    if not updates_batch:
                        break
                    
                    all_updates.extend(updates_batch)
                    offset = updates_batch[-1].update_id + 1
                    print(f"📊 Получено {len(updates_batch)} обновлений (попытка {attempt + 1})")
                    
                    # Если получили меньше чем лимит, значит это последняя порция
                    if len(updates_batch) < limit:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Ошибка получения обновлений (попытка {attempt + 1}): {e}")
                    break
            
            # Если нашли мало голосов, попробуем получить обновления с отрицательным offset
            if len(all_updates) < 100:
                print("⚠️ Получено мало обновлений, пытаемся получить более старые...")
                try:
                    # Получаем обновления с отрицательным offset (более старые)
                    for offset_val in [-200, -400, -600, -800, -1000]:
                        older_updates = await self.bot.get_updates(limit=200, offset=offset_val, timeout=10)
                        if older_updates:
                            all_updates.extend(older_updates)
                            print(f"📊 Получено дополнительно {len(older_updates)} старых обновлений (offset {offset_val})")
                        else:
                            break
                except Exception as e:
                    print(f"⚠️ Не удалось получить старые обновления: {e}")
            
            updates = all_updates
            print(f"📊 Всего получено {len(updates)} обновлений")
            
        except Exception as e:
            print(f"⚠️ Ошибка получения обновлений: {e}")
            updates = []
        
        # Получаем список уже существующих участников из Google таблицы
        existing_tuesday_voters = set()
        existing_friday_voters = set()
        
        try:
            worksheet = self.spreadsheet.worksheet("Тренировки")
            all_values = worksheet.get_all_values()
            
            # Ищем заголовки и собираем существующих участников
            for i, row in enumerate(all_values):
                if len(row) > 0 and row[0]:  # Если есть дата
                    # Проверяем, это заголовок вторника или пятницы
                    if len(row) > 1 and row[1] == "Вторник":
                        # Собираем участников вторника после этого заголовка
                        j = i + 1
                        while j < len(all_values) and all_values[j][1] != "Пятница" and all_values[j][1] != "Вторник":
                            if len(all_values[j]) > 3 and all_values[j][2] and all_values[j][3]:  # Есть имя и фамилия
                                name = all_values[j][3]  # Имя
                                surname = all_values[j][2]  # Фамилия
                                existing_tuesday_voters.add(f"{name} {surname}")
                            j += 1
                    elif len(row) > 1 and row[1] == "Пятница":
                        # Собираем участников пятницы после этого заголовка
                        j = i + 1
                        while j < len(all_values) and all_values[j][1] != "Вторник" and all_values[j][1] != "Пятница":
                            if len(all_values[j]) > 3 and all_values[j][2] and all_values[j][3]:  # Есть имя и фамилия
                                name = all_values[j][3]  # Имя
                                surname = all_values[j][2]  # Фамилия
                                existing_friday_voters.add(f"{name} {surname}")
                            j += 1
            
            print(f"📊 Найдено существующих участников вторника: {len(existing_tuesday_voters)}")
            print(f"📊 Найдено существующих участников пятницы: {len(existing_friday_voters)}")
            if existing_tuesday_voters:
                print(f"📊 Участники вторника: {', '.join(list(existing_tuesday_voters)[:5])}{'...' if len(existing_tuesday_voters) > 5 else ''}")
            if existing_friday_voters:
                print(f"📊 Участники пятницы: {', '.join(list(existing_friday_voters)[:5])}{'...' if len(existing_friday_voters) > 5 else ''}")
                
        except Exception as e:
            print(f"⚠️ Ошибка получения существующих участников: {e}")
        
        # Анализируем голоса
        tuesday_voters = []
        friday_voters = []
        trainer_voters = []
        no_voters = []
        
        poll_answers_found = 0
        total_poll_answers = 0
        user_votes = {}  # Для хранения последних голосов пользователей
        
        print(f"🔍 Анализ {len(updates)} обновлений...")
        
        # Сначала собираем все голоса пользователей
        for update in updates:
            if update.poll_answer:
                total_poll_answers += 1
                poll_answer = update.poll_answer
                user = update.effective_user
                
                print(f"🔍 Найден голос в опросе {poll_answer.poll_id} (ищем {poll_info['poll_id']})")
                
                if poll_answer.poll_id == poll_info['poll_id']:
                    # Сохраняем последний голос пользователя (перезаписываем предыдущий)
                    user_votes[user.id] = {
                        'user': user,
                        'option_ids': poll_answer.option_ids,
                        'update_id': update.update_id
                    }
                    print(f"📊 Голос пользователя {user.id}: варианты {poll_answer.option_ids}")
        
        print(f"📊 Найдено {len(user_votes)} уникальных пользователей с голосами")
        
        # Теперь обрабатываем последние голоса каждого пользователя
        for user_id, vote_data in user_votes.items():
            poll_answers_found += 1
            user = vote_data['user']
            option_ids = vote_data['option_ids']
            
            user_name = f"{user.first_name} {user.last_name or ''}".strip()
            telegram_id = user.username or "без_username"
            if telegram_id != "без_username":
                telegram_id = f"@{telegram_id}"
            
            # Форматируем имя игрока
            formatted_name = self.format_player_name(user_name, telegram_id)
            
            print(f"📊 Обрабатываем голос: {formatted_name} -> варианты {option_ids}")
            
            # Проверяем дубликаты по Google таблице
            # Распределяем по дням с проверкой дубликатов
            if 0 in option_ids:  # Вторник
                # Проверяем, есть ли уже этот участник в таблице для вторника
                name_parts = formatted_name.split()
                if len(name_parts) >= 2:
                    table_name = f"{name_parts[0]} {name_parts[-1]}"  # Имя Фамилия
                    if table_name not in existing_tuesday_voters:
                        tuesday_voters.append(formatted_name)
                        print(f"✅ Добавлен участник вторника: {formatted_name}")
                    else:
                        print(f"⚠️ Пропускаем дубликат вторника: {formatted_name} (уже есть в таблице)")
                else:
                    tuesday_voters.append(formatted_name)
                    print(f"✅ Добавлен участник вторника: {formatted_name}")
            
            if 1 in option_ids:  # Пятница
                # Проверяем, есть ли уже этот участник в таблице для пятницы
                name_parts = formatted_name.split()
                if len(name_parts) >= 2:
                    table_name = f"{name_parts[0]} {name_parts[-1]}"  # Имя Фамилия
                    if table_name not in existing_friday_voters:
                        friday_voters.append(formatted_name)
                        print(f"✅ Добавлен участник пятницы: {formatted_name}")
                    else:
                        print(f"⚠️ Пропускаем дубликат пятницы: {formatted_name} (уже есть в таблице)")
                else:
                    friday_voters.append(formatted_name)
                    print(f"✅ Добавлен участник пятницы: {formatted_name}")
            
            if 2 in option_ids:  # Тренер
                trainer_voters.append(formatted_name)
                print(f"✅ Добавлен тренер: {formatted_name}")
            
            if 3 in option_ids:  # Нет
                no_voters.append(formatted_name)
                print(f"✅ Добавлен 'Нет': {formatted_name}")
        
        print(f"📊 Всего голосов в обновлениях: {total_poll_answers}")
        print(f"📊 Голосов для нужного опроса: {poll_answers_found}")
        
        # Если нашли мало голосов, выводим предупреждение
        if poll_answers_found < 5:  # Если нашли меньше 5 голосов
            print("⚠️ Найдено мало голосов, возможно проблема с get_updates")
            print("⚠️ РЕШЕНИЕ: Увеличили лимит get_updates до 1000 обновлений")
            print("⚠️ Если проблема сохраняется, возможно голоса были сделаны давно")
            print("⚠️ ВАЖНО: Telegram API ограничивает количество обновлений, которые можно получить")
            print("⚠️ РЕКОМЕНДАЦИЯ: Собирайте данные опроса сразу после его создания")
        
        print(f"📊 Найдено {poll_answers_found} голосов для опроса {poll_info['poll_id']}")
        
        # Сохраняем результаты
        self.poll_results = {
            'poll_id': poll_info['poll_id'],
            'tuesday_voters': tuesday_voters,
            'friday_voters': friday_voters,
            'trainer_voters': trainer_voters,
            'no_voters': no_voters,
            'timestamp': self.get_moscow_time().isoformat()
        }
        
        with open('poll_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.poll_results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Данные собраны:")
        print(f"   Вторник: {len(tuesday_voters)} участников")
        print(f"   Пятница: {len(friday_voters)} участников")
        print(f"   Тренер: {len(trainer_voters)} участников")
        print(f"   Нет: {len(no_voters)} участников")
        
        # Логируем сбор данных
        try:
            if hasattr(self, '_log_data_collection'):
                self._log_data_collection(target_day)
            else:
                print("⚠️ Метод _log_data_collection не найден")
        except Exception as e:
            print(f"⚠️ Ошибка логирования сбора данных: {e}")
        
        # Сохраняем данные в Google Sheets
        try:
            if target_day.upper() == "ВТОРНИК" and tuesday_voters:
                print(f"💾 Сохранение данных за вторник в Google Sheets...")
                # Преобразуем данные для сохранения
                voters_for_sheet = []
                for voter_name in tuesday_voters:
                    # Парсим имя из строки "Имя Фамилия" (без username)
                    name_parts = voter_name.split()
                    if len(name_parts) >= 2:
                        surname = name_parts[-1]  # Последняя часть - фамилия
                        name = ' '.join(name_parts[:-1])  # Остальное - имя
                    else:
                        surname = name_parts[0] if name_parts else "Неизвестный"
                        name = "Неизвестный"
                    
                    # Для реальных данных используем имя как telegram_id
                    telegram_id = voter_name
                    
                    voters_for_sheet.append({
                        'surname': surname,
                        'name': name,
                        'telegram_id': telegram_id
                    })
                
                if voters_for_sheet:
                    self._save_voters_to_sheet("ВТОРНИК", voters_for_sheet, poll_info['poll_id'])
                else:
                    print("⚠️ Нет данных для сохранения за вторник")
            
            elif target_day.upper() == "ПЯТНИЦА" and friday_voters:
                print(f"💾 Сохранение данных за пятницу в Google Sheets...")
                # Аналогичная логика для пятницы
                voters_for_sheet = []
                for voter_name in friday_voters:
                    # Парсим имя из строки "Имя Фамилия" (без username)
                    name_parts = voter_name.split()
                    if len(name_parts) >= 2:
                        surname = name_parts[-1]
                        name = ' '.join(name_parts[:-1])
                    else:
                        surname = name_parts[0] if name_parts else "Неизвестный"
                        name = "Неизвестный"
                    
                    # Для реальных данных используем имя как telegram_id
                    telegram_id = voter_name
                    
                    voters_for_sheet.append({
                        'surname': surname,
                        'name': name,
                        'telegram_id': telegram_id
                    })
                
                if voters_for_sheet:
                    self._save_voters_to_sheet("ПЯТНИЦА", voters_for_sheet, poll_info['poll_id'])
                else:
                    print("⚠️ Нет данных для сохранения за пятницу")
                
        except Exception as e:
            print(f"⚠️ Ошибка сохранения данных в Google Sheets: {e}")
        
        return True

    def _save_voters_to_sheet(self, target_day: str, voters: List[Dict], poll_id: str) -> bool:
        """Сохраняет данные участников в Google Sheet с автоматической группировкой"""
        try:
            worksheet = self._get_or_create_training_worksheet()
            if not worksheet:
                print("❌ Не удалось получить лист 'Тренировки'")
                return False
            
            print(f"💾 Сохранение данных для {target_day}...")
            print(f"🔍 Тип voters: {type(voters)}")
            print(f"🔍 Содержимое voters: {voters}")
            
            if not isinstance(voters, list):
                print(f"❌ voters не является списком: {type(voters)}")
                return False
            
            print(f"💾 Сохранение {len(voters)} участников для {target_day}...")
            
            # Находим строки для соответствующего дня
            all_values = worksheet.get_all_values()
            target_day_upper = target_day.upper()
            
            # Ищем заголовок дня (Вторник или Пятница) в контексте опроса
            day_header_row = None
            poll_id = str(poll_id)
            
            # Сначала ищем строку с ID опроса
            poll_row = None
            for i, row in enumerate(all_values):
                if len(row) > 1 and row[1] == poll_id:
                    poll_row = i + 1
                    break
            
            if poll_row is None:
                print(f"❌ Не найден опрос с ID {poll_id}")
                return False
            
            print(f"✅ Найден опрос в строке {poll_row}")
            
            # Теперь ищем заголовок дня после строки опроса
            print(f"🔍 Поиск заголовка {target_day_upper} после строки {poll_row}...")
            for i in range(poll_row, len(all_values)):
                row_data = all_values[i]
                print(f"   Строка {i+1}: {row_data}")
                if len(row_data) > 1 and row_data[1].upper() == target_day_upper:
                    day_header_row = i + 1  # +1 потому что индексация в Google Sheets начинается с 1
                    print(f"✅ Найден заголовок {target_day_upper} в строке {day_header_row}")
                    break
            
            if day_header_row is None:
                print(f"❌ Не найден заголовок для дня {target_day_upper} после опроса {poll_id}")
                return False
            
            # Находим следующую строку после заголовка дня
            next_day_row = None
            for i in range(day_header_row, len(all_values)):
                if len(all_values[i]) > 1 and all_values[i][1] in ["Вторник", "Пятница"]:
                    next_day_row = i + 1
                    break
            
            if next_day_row is None:
                # Если это последний день, берем последнюю строку
                next_day_row = len(all_values) + 1
            
            # Вставляем участников после заголовка дня
            insert_row = day_header_row + 1
            
            # Подготавливаем данные для вставки
            rows_to_insert = []
            for voter in voters:
                # Получаем данные из словаря
                surname = voter.get('surname', 'Неизвестный')
                name = voter.get('name', 'игрок')
                telegram_id = voter.get('telegram_id', 'без_username')
                
                # Формат: ["", "", "Фамилия", "Имя", "Telegram ID"]
                row_data = ["", "", surname, name, telegram_id]
                rows_to_insert.append(row_data)
            
            # Вставляем все строки сразу
            if rows_to_insert:
                try:
                    print(f"🔧 Вставка {len(rows_to_insert)} строк начиная с позиции {insert_row}")
                    
                    # Вставляем строки по одной
                    for i, row_data in enumerate(rows_to_insert):
                        worksheet.insert_row(row_data, insert_row + i)
                    
                    print(f"✅ Сохранено {len(rows_to_insert)} участников для {target_day}")
                    
                    # Создаем автоматическую группировку
                    self._create_auto_grouping()
                    
                    return True
                except Exception as e:
                    print(f"❌ Ошибка при вставке строк: {e}")
                    return False
            else:
                print(f"⚠️ Нет участников для сохранения для {target_day}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка сохранения участников для {target_day}: {e}")
            return False

    def _create_auto_grouping(self) -> None:
        """Создает автоматическую группировку строк в Google Sheet"""
        try:
            if not self.spreadsheet:
                print("⚠️ Google Sheets не подключен, группировка не создана")
                return
            
            print("🔄 Создание автоматической группировки...")
            
            # Получаем лист "Тренировки"
            worksheet = self._get_or_create_training_worksheet()
            if not worksheet:
                print("❌ Не удалось получить лист для группировки")
                return
            
            # Получаем все данные
            all_values = worksheet.get_all_values()
            if len(all_values) < 7:
                print("⚠️ Недостаточно данных для группировки")
                return
            
            # Анализируем структуру и создаем группировку
            self._analyze_and_group_rows(worksheet, all_values)
            
            print("✅ Автоматическая группировка создана")
            
        except Exception as e:
            print(f"❌ Ошибка создания группировки: {e}")

    def _analyze_and_group_rows(self, worksheet, all_values: List[List[str]]) -> None:
        """Анализирует структуру данных и создает группировку строк"""
        try:
            # Находим ключевые строки
            poll_header_row = None
            tuesday_header_row = None
            friday_header_row = None
            tuesday_end_row = None
            friday_end_row = None
            
            for i, row in enumerate(all_values):
                if len(row) > 1:
                    if row[1] == "Вторник":
                        tuesday_header_row = i + 1
                    elif row[1] == "Пятница":
                        friday_header_row = i + 1
                    elif row[1] and row[1] != "Вторник" and row[1] != "Пятница" and row[2] and row[3]:
                        # Это участник
                        if tuesday_header_row and not tuesday_end_row:
                            tuesday_end_row = i + 1
                        elif friday_header_row and not friday_end_row:
                            friday_end_row = i + 1
            
            # Устанавливаем конец для последнего дня
            if tuesday_header_row and not tuesday_end_row:
                tuesday_end_row = len(all_values)
            if friday_header_row and not friday_end_row:
                friday_end_row = len(all_values)
            
            print(f"📋 Анализ структуры:")
            print(f"   Вторник: строки {tuesday_header_row}-{tuesday_end_row}")
            print(f"   Пятница: строки {friday_header_row}-{friday_end_row}")
            
            # Создаем группировку через Google Sheets API
            if tuesday_header_row and tuesday_end_row and friday_header_row and friday_end_row:
                self._create_row_grouping_via_api(worksheet, tuesday_header_row, tuesday_end_row, friday_header_row, friday_end_row)
            
        except Exception as e:
            print(f"❌ Ошибка анализа структуры: {e}")

    def _create_row_grouping_via_api(self, worksheet, tuesday_start: int, tuesday_end: int, friday_start: int, friday_end: int) -> None:
        """Создает группировку строк через Google Sheets API"""
        try:
            # Используем batch_update для создания группировки
            requests = []
            
            # 1. Группировка участников вторника
            if tuesday_start and tuesday_end and tuesday_end > tuesday_start:
                participants_range = f"{tuesday_start + 1}:{tuesday_end}"
                requests.append({
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": worksheet.id,
                            "dimension": "ROWS",
                            "startIndex": tuesday_start,
                            "endIndex": tuesday_end
                        }
                    }
                })
            
            # 2. Группировка участников пятницы
            if friday_start and friday_end and friday_end > friday_start:
                participants_range = f"{friday_start + 1}:{friday_end}"
                requests.append({
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": worksheet.id,
                            "dimension": "ROWS",
                            "startIndex": friday_start,
                            "endIndex": friday_end
                        }
                    }
                })
            
            # Применяем группировку
            if requests and self.spreadsheet:
                self.spreadsheet.batch_update({"requests": requests})
                print("✅ Группировка применена через API")
            
        except Exception as e:
            print(f"❌ Ошибка создания группировки через API: {e}")
            # Fallback: создаем простую группировку
            self._create_simple_grouping(worksheet, tuesday_start, tuesday_end, friday_start, friday_end)

    def _create_simple_grouping(self, worksheet, tuesday_start: int, tuesday_end: int, friday_start: int, friday_end: int) -> None:
        """Создает простую группировку через прямое управление строками"""
        try:
            # Создаем группировку для вторника
            if tuesday_start and tuesday_end and tuesday_end > tuesday_start:
                # Группируем участников под заголовком вторника
                for row_num in range(tuesday_start + 1, tuesday_end + 1):
                    try:
                        # Создаем группировку на уровне 1
                        worksheet.batch_update([{
                            "range": f"A{row_num}",
                            "values": [["", "", "", "", ""]]  # Пустая строка для группировки
                        }])
                    except Exception as e:
                        print(f"⚠️ Не удалось сгруппировать строку {row_num}: {e}")
            
            # Создаем группировку для пятницы
            if friday_start and friday_end and friday_end > friday_start:
                # Группируем участников под заголовком пятницы
                for row_num in range(friday_start + 1, friday_end + 1):
                    try:
                        # Создаем группировку на уровне 1
                        worksheet.batch_update([{
                            "range": f"A{row_num}",
                            "values": [["", "", "", "", ""]]  # Пустая строка для группировки
                        }])
                    except Exception as e:
                        print(f"⚠️ Не удалось сгруппировать строку {row_num}: {e}")
            
            print("✅ Простая группировка создана")
            
        except Exception as e:
            print(f"❌ Ошибка создания простой группировки: {e}")
    
    def _poll_exists(self) -> bool:
        """Проверяет, существует ли активный опрос для сбора данных"""
        try:
            if not self.spreadsheet:
                print("❌ Google Sheets не подключен")
                return False
            
            # Получаем лист 'Тренировки'
            try:
                worksheet = self.spreadsheet.worksheet("Тренировки")
            except gspread.WorksheetNotFound:
                print("❌ Лист 'Тренировки' не найден")
                return False
            
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:
                print("📄 Лист 'Тренировки' пустой")
                return False
            
            # Ищем активные опросы (строки с длинным ID в колонке 1)
            active_polls = []
            for i, row in enumerate(all_values):
                if len(row) > 1 and row[1] and len(row[1]) > 10 and row[1] not in ["Вторник", "Пятница"]:
                    active_polls.append({
                        'poll_id': row[1],
                        'date': row[0],
                        'row': i + 1
                    })
            
            if active_polls:
                latest_poll = active_polls[-1]  # Берем последний опрос
                print(f"✅ Активный опрос найден: {latest_poll['poll_id']} (дата: {latest_poll['date']})")
                return True
            else:
                print("📄 Активные опросы не найдены в Google Sheets")
                return False
            
        except Exception as e:
            print(f"⚠️ Ошибка проверки существования опроса: {e}")
            return False
    
    def save_to_training_sheet(self, target_day: str):
        """Сохраняет данные в лист 'Тренировки' с группировкой"""
        if not self.spreadsheet:
            print("❌ Google Sheets не подключен")
            return False
        
        try:
            # Загружаем результаты опроса
            if not os.path.exists('poll_results.json'):
                print("❌ Файл poll_results.json не найден")
                return False
            
            with open('poll_results.json', 'r', encoding='utf-8') as f:
                poll_results = json.load(f)
            
            # Загружаем информацию об опросе
            with open('current_poll_info.json', 'r', encoding='utf-8') as f:
                poll_info = json.load(f)
            
            # Получаем лист "Тренировки"
            try:
                worksheet = self.spreadsheet.worksheet("Тренировки")
                print("✅ Лист 'Тренировки' найден")
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(title="Тренировки", rows=1000, cols=10)
                print("✅ Лист 'Тренировки' создан")
                # Добавляем заголовки
                headers = ["Дата тренировки", "День недели", "Количество участников", "Участники"]
                worksheet.append_row(headers)
                # Форматируем заголовки
                worksheet.format('A1:D1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
            
            # Определяем данные для сохранения
            if target_day == "Вторник":
                voters = poll_results['tuesday_voters']
                training_date = poll_info['tuesday_date']
            elif target_day == "Пятница":
                voters = poll_results['friday_voters']
                training_date = poll_info['friday_date']
            else:
                print(f"❌ Неизвестный день: {target_day}")
                return False
            
            # Получаем все данные для определения следующей строки
            all_values = worksheet.get_all_values()
            next_row = len(all_values) + 1
            
            # Добавляем основную строку с группировкой
            main_row_data = [
                training_date,
                target_day,
                len(voters),
                ""  # Пустая колонка для участников
            ]
            worksheet.append_row(main_row_data)
            
            # Добавляем строки с участниками
            for voter in voters:
                participant_row = ["", "", "", voter]
                worksheet.append_row(participant_row)
            
            # Настраиваем группировку
            if len(voters) > 0:
                # Группируем строки с участниками
                start_row = next_row + 1
                end_row = next_row + len(voters)
                
                # Применяем группировку (если поддерживается API)
                try:
                    worksheet.batch_update([{
                        'range': f'A{start_row}:D{end_row}',
                        'properties': {
                            'hiddenByUser': True
                        }
                    }])
                except:
                    print("⚠️ Группировка не поддерживается в текущей версии API")
            
            print(f"✅ Данные за {target_day} сохранены:")
            print(f"   Дата тренировки: {training_date}")
            print(f"   Участников: {len(voters)}")
            print(f"   Участники: {', '.join(voters) if voters else 'нет'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в Google таблицу: {e}")
            return False

# Глобальный экземпляр
training_manager = TrainingPollsManager()

class TableIntegrityGuard:
    """Страж целостности таблицы - защита от дублирования"""
    
    def __init__(self, manager: TrainingPollsManager):
        self.manager = manager
        self.worksheet = None
        self.all_values = []
        self.structure_index = {}
    
    def load_table_data(self):
        """Загружает данные таблицы"""
        try:
            self.worksheet = self.manager._get_or_create_training_worksheet()
            if not self.worksheet:
                print("❌ Не удалось получить лист 'Тренировки'")
                return False
            
            self.all_values = self.worksheet.get_all_values()
            print(f"✅ Данные таблицы загружены: {len(self.all_values)} строк")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False
    
    def build_structure_index(self):
        """Строит индекс структуры таблицы"""
        if not self.all_values:
            print("❌ Данные таблицы не загружены")
            return False
        
        print("🔍 ПОСТРОЕНИЕ ИНДЕКСА СТРУКТУРЫ:")
        print("=" * 40)
        
        # Создаем индексы
        self.structure_index = {
            'polls': {},           # poll_id -> {row, date}
            'tuesday_sections': {}, # date -> {row, poll_id}
            'friday_sections': {},  # date -> {row, poll_id}
            'participants': {}      # day_date_surname_name -> row
        }
        
        current_poll_id = None
        
        for i, row in enumerate(self.all_values):
            if len(row) > 1:
                # Ищем опросы
                if row[1] and row[1] != "Вторник" and row[1] != "Пятница" and len(row[1]) > 10:
                    poll_id = row[1]
                    date = row[0]
                    self.structure_index['polls'][poll_id] = {'row': i + 1, 'date': date}
                    current_poll_id = poll_id
                    print(f"   📊 Опрос: {poll_id} (строка {i+1}, дата {date})")
                
                # Ищем заголовки дней
                elif row[1] == "Вторник":
                    date = row[0]
                    self.structure_index['tuesday_sections'][date] = {'row': i + 1, 'poll_id': current_poll_id}
                    print(f"   🏀 Вторник: {date} (строка {i+1}, опрос {current_poll_id})")
                
                elif row[1] == "Пятница":
                    date = row[0]
                    self.structure_index['friday_sections'][date] = {'row': i + 1, 'poll_id': current_poll_id}
                    print(f"   🏀 Пятница: {date} (строка {i+1}, опрос {current_poll_id})")
        
        print(f"✅ Индекс построен:")
        print(f"   📊 Опросов: {len(self.structure_index['polls'])}")
        print(f"   🏀 Секций вторника: {len(self.structure_index['tuesday_sections'])}")
        print(f"   🏀 Секций пятницы: {len(self.structure_index['friday_sections'])}")
        
        return True
    
    def check_poll_exists(self, poll_id: str) -> bool:
        """Проверяет существование опроса"""
        if poll_id in self.structure_index['polls']:
            info = self.structure_index['polls'][poll_id]
            print(f"⚠️ Опрос {poll_id} уже существует в строке {info['row']} (дата {info['date']})")
            return True
        return False
    
    def check_section_exists(self, target_day: str, date: str) -> bool:
        """Проверяет существование секции"""
        if target_day == "Вторник" and date in self.structure_index['tuesday_sections']:
            info = self.structure_index['tuesday_sections'][date]
            print(f"⚠️ Секция вторника для {date} уже существует в строке {info['row']}")
            return True
        elif target_day == "Пятница" and date in self.structure_index['friday_sections']:
            info = self.structure_index['friday_sections'][date]
            print(f"⚠️ Секция пятницы для {date} уже существует в строке {info['row']}")
            return True
        return False
    
    def check_participant_exists(self, target_day: str, date: str, surname: str, name: str) -> bool:
        """Проверяет существование участника"""
        # Ищем секцию
        section_info = None
        if target_day == "Вторник":
            section_info = self.structure_index['tuesday_sections'].get(date)
        elif target_day == "Пятница":
            section_info = self.structure_index['friday_sections'].get(date)
        
        if not section_info:
            return False
        
        section_row = section_info['row']
        
        # Проверяем участников под заголовком
        for i in range(section_row, len(self.all_values)):
            row = self.all_values[i]
            if len(row) >= 5 and row[2] and row[3]:
                if row[2] == surname and row[3] == name:
                    print(f"⚠️ Участник {surname} {name} уже существует в {target_day} {date} (строка {i+1})")
                    return True
            elif len(row) > 1 and row[1] in ["Вторник", "Пятница"]:
                # Достигли следующего заголовка
                break
        
        return False
    
    def safe_add_poll(self, poll_id: str, date: str) -> dict:
        """Безопасно добавляет опрос"""
        print(f"\n🔧 БЕЗОПАСНОЕ ДОБАВЛЕНИЕ ОПРОСА:")
        print("=" * 40)
        
        result = {
            'success': False,
            'reason': '',
            'action': 'none'
        }
        
        # Проверяем дублирование
        if self.check_poll_exists(poll_id):
            result['reason'] = f"Опрос {poll_id} уже существует"
            result['action'] = 'skip'
            print(f"❌ Опрос {poll_id} не добавлен - дубликат")
            return result
        
        # Проверяем дублирование даты
        for poll_info in self.structure_index['polls'].values():
            if poll_info['date'] == date:
                result['reason'] = f"Опрос для {date} уже существует"
                result['action'] = 'skip'
                print(f"❌ Опрос для {date} не добавлен - дата уже существует")
                return result
        
        result['success'] = True
        result['action'] = 'add'
        print(f"✅ Опрос {poll_id} для {date} готов к добавлению")
        return result
    
    def safe_add_section(self, target_day: str, date: str, poll_id: str) -> dict:
        """Безопасно добавляет секцию"""
        print(f"\n🔧 БЕЗОПАСНОЕ ДОБАВЛЕНИЕ СЕКЦИИ {target_day.upper()}:")
        print("=" * 40)
        
        result = {
            'success': False,
            'reason': '',
            'action': 'none'
        }
        
        # Проверяем дублирование секции
        if self.check_section_exists(target_day, date):
            result['reason'] = f"Секция {target_day} для {date} уже существует"
            result['action'] = 'skip'
            print(f"❌ Секция {target_day} для {date} не добавлена - дубликат")
            return result
        
        # Проверяем существование опроса
        if poll_id not in self.structure_index['polls']:
            result['reason'] = f"Опрос {poll_id} не найден"
            result['action'] = 'error'
            print(f"❌ Секция {target_day} для {date} не добавлена - опрос {poll_id} не найден")
            return result
        
        result['success'] = True
        result['action'] = 'add'
        print(f"✅ Секция {target_day} для {date} (опрос {poll_id}) готова к добавлению")
        return result
    
    def safe_add_participant(self, target_day: str, date: str, surname: str, name: str, telegram_id: str) -> dict:
        """Безопасно добавляет участника"""
        print(f"\n🔧 БЕЗОПАСНОЕ ДОБАВЛЕНИЕ УЧАСТНИКА:")
        print("=" * 40)
        
        result = {
            'success': False,
            'reason': '',
            'action': 'none'
        }
        
        # Проверяем дублирование участника
        if self.check_participant_exists(target_day, date, surname, name):
            result['reason'] = f"Участник {surname} {name} уже существует в {target_day} {date}"
            result['action'] = 'skip'
            print(f"❌ Участник {surname} {name} не добавлен - дубликат")
            return result
        
        # Проверяем существование секции
        section_exists = False
        if target_day == "Вторник":
            section_exists = date in self.structure_index['tuesday_sections']
        elif target_day == "Пятница":
            section_exists = date in self.structure_index['friday_sections']
        
        if not section_exists:
            result['reason'] = f"Секция {target_day} для {date} не найдена"
            result['action'] = 'error'
            print(f"❌ Участник {surname} {name} не добавлен - секция {target_day} для {date} не найдена")
            return result
        
        result['success'] = True
        result['action'] = 'add'
        print(f"✅ Участник {surname} {name} ({telegram_id}) готов к добавлению в {target_day} {date}")
        return result
    
    def get_integrity_report(self):
        """Генерирует отчет о целостности"""
        print(f"\n📊 ОТЧЕТ О ЦЕЛОСТНОСТИ ТАБЛИЦЫ:")
        print("=" * 50)
        
        issues = []
        
        # Проверяем опросы
        print(f"📊 ОПРОСЫ:")
        for poll_id, info in self.structure_index['polls'].items():
            print(f"   ✅ {poll_id} (строка {info['row']}, дата {info['date']})")
        
        # Проверяем секции вторника
        print(f"\n🏀 СЕКЦИИ ВТОРНИКА:")
        for date, info in self.structure_index['tuesday_sections'].items():
            poll_id = info['poll_id'] or "без опроса"
            print(f"   ✅ {date} (строка {info['row']}, опрос {poll_id})")
            if not info['poll_id']:
                issues.append(f"Секция вторника {date} не связана с опросом")
        
        # Проверяем секции пятницы
        print(f"\n🏀 СЕКЦИИ ПЯТНИЦЫ:")
        for date, info in self.structure_index['friday_sections'].items():
            poll_id = info['poll_id'] or "без опроса"
            print(f"   ✅ {date} (строка {info['row']}, опрос {poll_id})")
            if not info['poll_id']:
                issues.append(f"Секция пятницы {date} не связана с опросом")
        
        if not issues:
            print(f"\n🎉 ЦЕЛОСТНОСТЬ ТАБЛИЦЫ: ОТЛИЧНО!")
        else:
            print(f"\n⚠️ ЦЕЛОСТНОСТЬ ТАБЛИЦЫ: {len(issues)} ПРОБЛЕМ!")
            for issue in issues:
                print(f"   • {issue}")
        
        return len(issues) == 0

# Глобальный экземпляр стража целостности
integrity_guard = TableIntegrityGuard(training_manager)

async def main():
    """Основная функция"""
    print("🏀 СИСТЕМА УПРАВЛЕНИЯ ОПРОСАМИ ТРЕНИРОВОК")
    print("=" * 60)
    
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 День недели: {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()]}")
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print("�� ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    print(f"GOOGLE_CREDENTIALS_FILE: {'✅' if os.path.exists('google_credentials.json') else '❌'}")
    
    if not all([bot_token, chat_id, spreadsheet_id]):
        print("❌ Не все переменные окружения настроены")
        return
    
    print(f"✅ SPREADSHEET_ID: {spreadsheet_id}")
    
    # Проверяем условия выполнения
    print("\n🔍 ПРОВЕРКА УСЛОВИЙ ВЫПОЛНЕНИЯ:")
    print(f"   Создание опроса (воскресенье 10:00): {'✅' if training_manager.should_create_weekly_poll() else '❌'}")
    print(f"   Сбор данных за вторник (среда 10:00): {'✅' if training_manager.should_collect_tuesday_data() else '❌'}")
    print(f"   Сбор данных за пятницу (суббота 10:00): {'✅' if training_manager.should_collect_friday_data() else '❌'}")
    
    # Проверяем, что нужно сделать
    if training_manager.should_create_weekly_poll():
        print("\n🔄 Создание еженедельного опроса...")
        success = await training_manager.create_weekly_training_poll()
        if success:
            print("✅ Еженедельный опрос создан успешно")
        else:
            print("❌ Ошибка создания опроса")
    
    elif training_manager.should_collect_tuesday_data():
        print("\n🔄 Сбор данных за вторник...")
        success = await training_manager.collect_poll_data("Вторник")
        if success:
            print("✅ Данные за вторник собраны и сохранены")
        else:
            print("❌ Ошибка сбора данных за вторник")
    
    elif training_manager.should_collect_friday_data():
        print("\n🔄 Сбор данных за пятницу...")
        success = await training_manager.collect_poll_data("Пятница")
        if success:
            print("✅ Данные за пятницу собраны и сохранены")
        else:
            print("❌ Ошибка сбора данных за пятницу")
    
    else:
        print("\n⏰ Не время для выполнения операций")
        print("📅 Расписание:")
        print("   🗓️ Воскресенье 10:00-23:59 - Создание опроса")
        print("   📊 Среда 10:00-23:59 - Сбор данных за вторник")
        print("   📊 Суббота 10:00-23:59 - Сбор данных за пятницу")

if __name__ == "__main__":
    asyncio.run(main())
