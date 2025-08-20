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



def get_next_tuesday_date():
    """Возвращает дату следующего вторника"""
    now = get_moscow_time()
    days_ahead = 1 - now.weekday()  # 1 = вторник
    if days_ahead <= 0:  # Если сегодня вторник или позже
        days_ahead += 7
    next_tuesday = now + datetime.timedelta(days=days_ahead)
    return next_tuesday.date()

def get_next_friday_date():
    """Возвращает дату следующей пятницы"""
    now = get_moscow_time()
    days_ahead = 4 - now.weekday()  # 4 = пятница
    if days_ahead <= 0:  # Если сегодня пятница или позже
        days_ahead += 7
    next_friday = now + datetime.timedelta(days=days_ahead)
    return next_friday.date()

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
            if not GOOGLE_SHEETS_CREDENTIALS:
                print("⚠️ GOOGLE_SHEETS_CREDENTIALS не настроен")
                return
            
            creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
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
            # Получаем даты тренировок
            tuesday_date = get_next_tuesday_date()
            friday_date = get_next_friday_date()
            
            # Формируем вопрос и варианты
            question = f"🏀 Тренировки на неделе СШОР ВО ({tuesday_date.strftime('%d.%m')} - {friday_date.strftime('%d.%m')})"
            options = [
                f"🏀 Вторник {tuesday_date.strftime('%d.%m')} 19:00",
                f"🏀 Пятница {friday_date.strftime('%d.%m')} 20:30",
                "👨‍🏫 Тренер",
                "❌ Нет"
            ]
            
            # Отправляем опрос
            message_thread_id = int(ANNOUNCEMENTS_TOPIC_ID) if ANNOUNCEMENTS_TOPIC_ID else None
            
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
                'date': get_moscow_time().isoformat(),
                'chat_id': CHAT_ID,
                'topic_id': ANNOUNCEMENTS_TOPIC_ID,
                'tuesday_date': tuesday_date.isoformat(),
                'friday_date': friday_date.isoformat()
            }
            
            # Сохраняем в файл
            with open('current_poll_info.json', 'w', encoding='utf-8') as f:
                json.dump(self.current_poll_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Опрос создан успешно")
            print(f"📊 ID опроса: {self.current_poll_info['poll_id']}")
            print(f"📅 Вторник: {tuesday_date.strftime('%d.%m.%Y')}")
            print(f"📅 Пятница: {friday_date.strftime('%d.%m.%Y')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса: {e}")
            return False
    
    def should_create_weekly_poll(self):
        """Проверяет, нужно ли создавать еженедельный опрос"""
        now = get_moscow_time()
        
        # Создаем опрос каждое воскресенье в 10:00-10:59
        if now.weekday() == 6 and now.hour == 10:
            # Проверяем, не был ли уже создан опрос сегодня
            if self._was_poll_created_today():
                print("📊 Опрос уже был создан сегодня")
                return False
            return True
        
        return False
    
    def _was_poll_created_today(self) -> bool:
        """Проверяет, был ли уже создан опрос сегодня"""
        try:
            if not os.path.exists('current_poll_info.json'):
                return False
            
            with open('current_poll_info.json', 'r', encoding='utf-8') as f:
                poll_info = json.load(f)
            
            # Получаем дату создания опроса
            poll_date_str = poll_info.get('date', '')
            if not poll_date_str:
                return False
            
            # Парсим дату создания опроса
            poll_date = datetime.datetime.fromisoformat(poll_date_str.replace('Z', '+00:00'))
            poll_date_moscow = poll_date.replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=3))
            )
            
            # Сравниваем с сегодняшней датой
            today = get_moscow_time().date()
            poll_date_only = poll_date_moscow.date()
            
            if poll_date_only == today:
                print(f"📊 Опрос уже создан сегодня: {poll_date_moscow.strftime('%Y-%m-%d %H:%M')}")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка проверки даты создания опроса: {e}")
            return False
    
    def should_collect_tuesday_data(self):
        """Проверяет, нужно ли собирать данные за вторник"""
        now = get_moscow_time()
        
        # Собираем данные каждую среду в 10:00-10:59
        if now.weekday() == 2 and now.hour == 10:
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
        now = get_moscow_time()
        
        # Собираем данные каждую субботу в 10:00-10:59
        if now.weekday() == 5 and now.hour == 10:
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
            
            today = get_moscow_time().date().isoformat()
            
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
            now = get_moscow_time()
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
    
    def get_player_full_name(self, player_data: Dict) -> str:
        """Получает полное имя игрока"""
        if not player_data:
            return None
        
        headers = player_data['headers']
        data = player_data['data']
        
        # Ищем колонки с именем и фамилией
        name_col = None
        surname_col = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'имя' in header_lower or 'name' in header_lower:
                name_col = i
            elif 'фамилия' in header_lower or 'surname' in header_lower or 'last' in header_lower:
                surname_col = i
        
        # Формируем полное имя
        full_name_parts = []
        
        if surname_col is not None and len(data) > surname_col:
            surname = data[surname_col].strip()
            if surname:
                full_name_parts.append(surname)
        
        if name_col is not None and len(data) > name_col:
            name = data[name_col].strip()
            if name:
                full_name_parts.append(name)
        
        if full_name_parts:
            return ' '.join(full_name_parts)
        else:
            return None
    
    def format_player_name(self, user_name: str, telegram_id: str) -> str:
        """Форматирует имя игрока с учетом данных из таблицы"""
        # Убираем @ из telegram_id для поиска
        clean_telegram_id = telegram_id.replace('@', '')
        
        # Ищем игрока в таблице
        player_data = self.find_player_by_telegram_id(clean_telegram_id)
        
        if player_data:
            full_name = self.get_player_full_name(player_data)
            if full_name:
                return full_name
        
        # Если не найден, возвращаем имя и telegram_id
        return f"{user_name} ({telegram_id})"
    
    async def collect_poll_data(self, target_day: str):
        """Собирает данные опроса для указанного дня"""
        print(f"🔍 Начинаем сбор данных за {target_day}")
        
        if not os.path.exists('current_poll_info.json'):
            print("❌ Файл current_poll_info.json не найден")
            return False
        
        # Проверяем размер файла
        file_size = os.path.getsize('current_poll_info.json')
        print(f"📄 Размер файла current_poll_info.json: {file_size} байт")
        
        if file_size == 0:
            print("❌ Файл current_poll_info.json пустой")
            return False
        
        try:
            # Загружаем информацию об опросе
            with open('current_poll_info.json', 'r', encoding='utf-8') as f:
                poll_info = json.load(f)
            
            # Проверяем, есть ли poll_id в файле
            if not poll_info or 'poll_id' not in poll_info:
                print(f"❌ Файл current_poll_info.json не содержит poll_id")
                print(f"📄 Содержимое файла: {poll_info}")
                return False
            
            print(f"📊 Сбор данных за {target_day}")
            print(f"📊 ID опроса: {poll_info['poll_id']}")
            
            # Получаем обновления от бота
            updates = await self.bot.get_updates(limit=50)
            
            # Анализируем голоса
            tuesday_voters = []
            friday_voters = []
            trainer_voters = []
            no_voters = []
            
            for update in updates:
                if update.poll_answer:
                    poll_answer = update.poll_answer
                    if poll_answer.poll_id == poll_info['poll_id']:
                        user = poll_answer.user
                        option_ids = poll_answer.option_ids
                        
                        user_name = f"{user.first_name} {user.last_name or ''}".strip()
                        telegram_id = user.username or "без_username"
                        if telegram_id != "без_username":
                            telegram_id = f"@{telegram_id}"
                        
                        # Форматируем имя игрока
                        formatted_name = self.format_player_name(user_name, telegram_id)
                        
                        # Распределяем по дням
                        if 0 in option_ids:  # Вторник
                            tuesday_voters.append(formatted_name)
                        if 1 in option_ids:  # Пятница
                            friday_voters.append(formatted_name)
                        if 2 in option_ids:  # Тренер
                            trainer_voters.append(formatted_name)
                        if 3 in option_ids:  # Нет
                            no_voters.append(formatted_name)
            
            # Сохраняем результаты
            self.poll_results = {
                'poll_id': poll_info['poll_id'],
                'tuesday_voters': tuesday_voters,
                'friday_voters': friday_voters,
                'trainer_voters': trainer_voters,
                'no_voters': no_voters,
                'timestamp': get_moscow_time().isoformat()
            }
            
            with open('poll_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.poll_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Данные собраны:")
            print(f"   Вторник: {len(tuesday_voters)} участников")
            print(f"   Пятница: {len(friday_voters)} участников")
            print(f"   Тренер: {len(trainer_voters)} участников")
            print(f"   Нет: {len(no_voters)} участников")
            
            # Логируем сбор данных
            self._log_data_collection(target_day)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сбора данных: {e}")
            return False
    
    def _poll_exists(self) -> bool:
        """Проверяет, существует ли активный опрос для сбора данных"""
        try:
            if not os.path.exists('current_poll_info.json'):
                print("📄 Файл current_poll_info.json не найден")
                return False
            
            # Проверяем размер файла
            file_size = os.path.getsize('current_poll_info.json')
            if file_size <= 3:  # Файл пустой или содержит только {}
                print("📄 Файл current_poll_info.json пустой")
                return False
            
            with open('current_poll_info.json', 'r', encoding='utf-8') as f:
                poll_info = json.load(f)
            
            # Проверяем наличие poll_id
            if not poll_info or 'poll_id' not in poll_info:
                print("📄 Файл current_poll_info.json не содержит poll_id")
                return False
            
            print(f"✅ Активный опрос найден: {poll_info['poll_id']}")
            return True
            
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
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
    print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    
    if not all([bot_token, chat_id, google_credentials, spreadsheet_id]):
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
            print("✅ Данные за вторник собраны")
            save_success = training_manager.save_to_training_sheet("Вторник")
            if save_success:
                print("✅ Данные за вторник сохранены в таблицу")
            else:
                print("❌ Ошибка сохранения данных за вторник")
        else:
            print("❌ Ошибка сбора данных за вторник")
    
    elif training_manager.should_collect_friday_data():
        print("\n🔄 Сбор данных за пятницу...")
        success = await training_manager.collect_poll_data("Пятница")
        if success:
            print("✅ Данные за пятницу собраны")
            save_success = training_manager.save_to_training_sheet("Пятница")
            if save_success:
                print("✅ Данные за пятницу сохранены в таблицу")
            else:
                print("❌ Ошибка сохранения данных за пятницу")
        else:
            print("❌ Ошибка сбора данных за пятницу")
    
    else:
        print("\n⏰ Не время для выполнения операций")
        print("📅 Расписание:")
        print("   🗓️ Воскресенье 10:00 - Создание опроса")
        print("   📊 Среда 10:00 - Сбор данных за вторник")
        print("   📊 Суббота 10:00 - Сбор данных за пятницу")

if __name__ == "__main__":
    asyncio.run(main())
