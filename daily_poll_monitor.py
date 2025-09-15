#!/usr/bin/env python3
"""
Ежедневный мониторинг голосований за тренировки
Проверяет изменения в голосах каждый день и обновляет Google таблицу
"""

import os
import asyncio
import datetime
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from dotenv import load_dotenv
from telegram import Bot
import gspread
from datetime_utils import get_moscow_time, log_current_time
from google.oauth2.service_account import Credentials

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Настройки Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class DailyPollMonitor:
    """Ежедневный мониторинг голосований за тренировки"""
    
    def __init__(self):
        self.bot = None
        self.spreadsheet = None
        self.worksheet = None
        self.current_votes = {}  # Текущие голоса {user_id: {name, options, day}}
        self.previous_votes = {}  # Предыдущие голоса для сравнения
        
    async def initialize(self):
        """Инициализация бота и Google Sheets"""
        try:
            # Инициализация Telegram бота
            if BOT_TOKEN:
                self.bot = Bot(token=BOT_TOKEN)
                print("✅ Telegram бот инициализирован")
            else:
                print("❌ BOT_TOKEN не найден")
                return False
            
            # Инициализация Google Sheets
            if GOOGLE_SHEETS_CREDENTIALS and SPREADSHEET_ID:
                credentials_info = json.loads(GOOGLE_SHEETS_CREDENTIALS)
                credentials = Credentials.from_service_account_info(
                    credentials_info, scopes=SCOPES
                )
                gc = gspread.authorize(credentials)
                self.spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                
                # Получаем лист "Тренировки"
                try:
                    self.worksheet = self.spreadsheet.worksheet("Тренировки")
                    print("✅ Google Sheets подключен")
                except gspread.WorksheetNotFound:
                    print("❌ Лист 'Тренировки' не найден")
                    return False
            else:
                print("❌ Google Sheets не настроен")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def get_active_polls_info(self) -> Dict[str, Any]:
        """Определяет активные опросы на основе дня недели"""
        now = get_moscow_time()
        weekday = now.weekday()  # 0=понедельник, 6=воскресенье
        
        active_polls = {}
        
        # Новая логика активных опросов:
        # Воскресенье (6): создается опрос на неделю
        # Понедельник-среда (0-2): проверка за вторник
        # Четверг-суббота (3-5): проверка за пятницу
        
        if weekday >= 0 and weekday <= 2:  # Понедельник-среда
            active_polls['tuesday'] = {
                'day': 'Вторник',
                'active': True,
                'period': 'понедельник-среда',
                'ends': 'среда'
            }
        
        if weekday >= 3 and weekday <= 5:  # Четверг-суббота
            active_polls['friday'] = {
                'day': 'Пятница', 
                'active': True,
                'period': 'четверг-суббота',
                'ends': 'суббота'
            }
        
        return active_polls
    
    async def find_active_training_poll(self) -> Optional[str]:
        """Ищет активный опрос тренировок из системы защиты от дублирования"""
        try:
            # Импортируем систему защиты от дублирования
            from enhanced_duplicate_protection import duplicate_protection
            
            # Получаем все записи опросов тренировок
            training_polls = duplicate_protection.get_records_by_type("ОПРОС_ТРЕНИРОВКА")
            
            if not training_polls:
                print("⚠️ Опросы тренировок не найдены в системе защиты от дублирования")
                return None
            
            # Ищем самый последний активный опрос
            latest_poll = None
            latest_date = None
            
            for poll in training_polls:
                poll_date = poll.get('date', '')
                poll_status = poll.get('status', '')
                poll_id = poll.get('unique_key', '')
                
                # Ищем активные опросы
                if poll_status == 'АКТИВЕН' and poll_id:
                    # Извлекаем poll_id из unique_key (формат: ОПРОС_ТРЕНИРОВКА_poll_id)
                    if poll_id.startswith('ОПРОС_ТРЕНИРОВКА_'):
                        actual_poll_id = poll_id.replace('ОПРОС_ТРЕНИРОВКА_', '')
                        
                        # Сравниваем даты для поиска самого последнего
                        if not latest_date or poll_date > latest_date:
                            latest_poll = actual_poll_id
                            latest_date = poll_date
            
            if latest_poll:
                print(f"✅ Найден активный опрос тренировок: {latest_poll}")
                print(f"📅 Дата создания: {latest_date}")
                return latest_poll
            else:
                print("⚠️ Активные опросы тренировок не найдены")
                return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска активного опроса: {e}")
            return None

    async def get_current_poll_votes(self, poll_id: str) -> Dict[int, Dict]:
        """Получает текущие голоса для конкретного опроса"""
        if not self.bot:
            return {}
        
        try:
            # Получаем обновления от бота
            updates = await self.bot.get_updates(limit=100, timeout=10)
            
            current_votes = {}
            
            for update in updates:
                if update.poll_answer and update.poll_answer.poll_id == poll_id:
                    user = update.effective_user
                    user_name = f"{user.first_name} {user.last_name or ''}".strip()
                    telegram_id = user.username or "без_username"
                    if telegram_id != "без_username":
                        telegram_id = f"@{telegram_id}"
                    
                    # Форматируем имя
                    formatted_name = self.format_player_name(user_name, telegram_id)
                    
                    current_votes[user.id] = {
                        'name': formatted_name,
                        'options': update.poll_answer.option_ids,
                        'update_id': update.update_id
                    }
            
            return current_votes
            
        except Exception as e:
            print(f"❌ Ошибка получения голосов для опроса {poll_id}: {e}")
            return {}
    
    def format_player_name(self, user_name: str, telegram_id: str) -> str:
        """Форматирует имя игрока"""
        if not user_name or user_name.strip() == "":
            return telegram_id
        
        # Убираем лишние пробелы
        name_parts = user_name.strip().split()
        if len(name_parts) >= 2:
            return f"{name_parts[0]} {name_parts[-1]}"
        else:
            return name_parts[0] if name_parts else telegram_id
    
    def load_previous_votes(self, poll_id: str) -> Dict[int, Dict]:
        """Загружает предыдущие голоса из файла"""
        try:
            filename = f"poll_votes_{poll_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки предыдущих голосов: {e}")
        
        return {}
    
    def save_current_votes(self, poll_id: str, votes: Dict[int, Dict]):
        """Сохраняет текущие голоса в файл"""
        try:
            filename = f"poll_votes_{poll_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(votes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения голосов: {e}")
    
    def find_vote_changes(self, previous_votes: Dict[int, Dict], current_votes: Dict[int, Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Находит изменения в голосах"""
        added_votes = []      # Новые голоса
        removed_votes = []    # Удаленные голоса  
        changed_votes = []    # Измененные голоса
        
        # Проверяем новые и измененные голоса
        for user_id, current_vote in current_votes.items():
            if user_id not in previous_votes:
                # Новый голос
                added_votes.append(current_vote)
            else:
                # Проверяем, изменился ли голос
                previous_vote = previous_votes[user_id]
                if current_vote['options'] != previous_vote['options']:
                    changed_votes.append({
                        'previous': previous_vote,
                        'current': current_vote
                    })
        
        # Проверяем удаленные голоса
        for user_id, previous_vote in previous_votes.items():
            if user_id not in current_votes:
                removed_votes.append(previous_vote)
        
        return added_votes, removed_votes, changed_votes
    
    def get_existing_voters_from_sheet(self, day: str) -> Set[str]:
        """Получает существующих участников из Google таблицы для конкретного дня"""
        existing_voters = set()
        
        try:
            all_values = self.worksheet.get_all_values()
            
            for i, row in enumerate(all_values):
                if len(row) > 1 and row[1] == day:
                    # Нашли заголовок дня, собираем участников
                    j = i + 1
                    while j < len(all_values):
                        next_row = all_values[j]
                        # Если встретили другой заголовок дня, останавливаемся
                        if len(next_row) > 1 and next_row[1] in ["Вторник", "Пятница"]:
                            break
                        
                        # Если есть имя и фамилия
                        if len(next_row) > 3 and next_row[2] and next_row[3]:
                            name = next_row[3]  # Имя
                            surname = next_row[2]  # Фамилия
                            existing_voters.add(f"{name} {surname}")
                        
                        j += 1
                    break
            
        except Exception as e:
            print(f"⚠️ Ошибка получения существующих участников: {e}")
        
        return existing_voters
    
    def add_voter_to_sheet(self, voter_name: str, day: str) -> bool:
        """Добавляет участника в Google таблицу"""
        try:
            # Находим строку для вставки
            all_values = self.worksheet.get_all_values()
            insert_row = None
            
            for i, row in enumerate(all_values):
                if len(row) > 1 and row[1] == day:
                    # Нашли заголовок дня, ищем место для вставки
                    j = i + 1
                    while j < len(all_values):
                        next_row = all_values[j]
                        # Если встретили другой заголовок дня, вставляем перед ним
                        if len(next_row) > 1 and next_row[1] in ["Вторник", "Пятница"]:
                            insert_row = j + 1  # +1 потому что нумерация строк начинается с 1
                            break
                        # Если пустая строка, вставляем туда
                        if not any(next_row[2:5]):  # Проверяем колонки C, D, E
                            insert_row = j + 1
                            break
                        j += 1
                    
                    if insert_row is None:
                        insert_row = j + 1  # Вставляем в конец
                    break
            
            if insert_row:
                # Разбиваем имя на части
                name_parts = voter_name.split()
                if len(name_parts) >= 2:
                    surname = name_parts[-1]
                    first_name = " ".join(name_parts[:-1])
                else:
                    surname = voter_name
                    first_name = ""
                
                # Вставляем строку
                self.worksheet.insert_row([
                    "",  # A - пустая колонка
                    "",  # B - пустая колонка  
                    surname,  # C - фамилия
                    first_name,  # D - имя
                    ""   # E - пустая колонка
                ], insert_row)
                
                print(f"✅ Добавлен участник {voter_name} в {day}")
                return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления участника {voter_name}: {e}")
        
        return False
    
    def remove_voter_from_sheet(self, voter_name: str, day: str) -> bool:
        """Удаляет участника из Google таблицы"""
        try:
            all_values = self.worksheet.get_all_values()
            
            for i, row in enumerate(all_values):
                if len(row) > 1 and row[1] == day:
                    # Нашли заголовок дня, ищем участника
                    j = i + 1
                    while j < len(all_values):
                        next_row = all_values[j]
                        # Если встретили другой заголовок дня, останавливаемся
                        if len(next_row) > 1 and next_row[1] in ["Вторник", "Пятница"]:
                            break
                        
                        # Проверяем, это ли наш участник
                        if len(next_row) > 3 and next_row[2] and next_row[3]:
                            name = next_row[3]  # Имя
                            surname = next_row[2]  # Фамилия
                            table_name = f"{name} {surname}"
                            
                            if table_name == voter_name:
                                # Удаляем строку (j+1 потому что нумерация начинается с 1)
                                self.worksheet.delete_rows(j + 1)
                                print(f"✅ Удален участник {voter_name} из {day}")
                                return True
                        
                        j += 1
                    break
            
        except Exception as e:
            print(f"❌ Ошибка удаления участника {voter_name}: {e}")
        
        return False
    
    async def process_poll_changes(self, poll_id: str, day: str):
        """Обрабатывает изменения в голосовании для конкретного дня"""
        print(f"🔍 Обработка изменений для {day} (опрос {poll_id})")
        
        # Получаем текущие голоса
        current_votes = await self.get_current_poll_votes(poll_id)
        
        # Загружаем предыдущие голоса
        previous_votes = self.load_previous_votes(poll_id)
        
        # Находим изменения
        added_votes, removed_votes, changed_votes = self.find_vote_changes(previous_votes, current_votes)
        
        print(f"📊 Изменения для {day}:")
        print(f"   Новые голоса: {len(added_votes)}")
        print(f"   Удаленные голоса: {len(removed_votes)}")
        print(f"   Измененные голоса: {len(changed_votes)}")
        
        # Обрабатываем изменения
        changes_made = False
        
        # Добавляем новые голоса
        for vote in added_votes:
            if 0 in vote['options'] and day == 'Вторник':  # Голос за вторник
                if self.add_voter_to_sheet(vote['name'], day):
                    changes_made = True
            elif 1 in vote['options'] and day == 'Пятница':  # Голос за пятницу
                if self.add_voter_to_sheet(vote['name'], day):
                    changes_made = True
        
        # Удаляем пропавшие голоса
        for vote in removed_votes:
            if 0 in vote['options'] and day == 'Вторник':  # Был голос за вторник
                if self.remove_voter_from_sheet(vote['name'], day):
                    changes_made = True
            elif 1 in vote['options'] and day == 'Пятница':  # Был голос за пятницу
                if self.remove_voter_from_sheet(vote['name'], day):
                    changes_made = True
        
        # Обрабатываем измененные голоса
        for change in changed_votes:
            previous_vote = change['previous']
            current_vote = change['current']
            
            # Если раньше голосовал за этот день, а теперь нет - удаляем
            if 0 in previous_vote['options'] and day == 'Вторник' and 0 not in current_vote['options']:
                if self.remove_voter_from_sheet(previous_vote['name'], day):
                    changes_made = True
            elif 1 in previous_vote['options'] and day == 'Пятница' and 1 not in current_vote['options']:
                if self.remove_voter_from_sheet(previous_vote['name'], day):
                    changes_made = True
            
            # Если раньше не голосовал за этот день, а теперь голосует - добавляем
            if 0 not in previous_vote['options'] and day == 'Вторник' and 0 in current_vote['options']:
                if self.add_voter_to_sheet(current_vote['name'], day):
                    changes_made = True
            elif 1 not in previous_vote['options'] and day == 'Пятница' and 1 in current_vote['options']:
                if self.add_voter_to_sheet(current_vote['name'], day):
                    changes_made = True
        
        # Сохраняем текущие голоса как предыдущие для следующей проверки
        self.save_current_votes(poll_id, current_votes)
        
        if changes_made:
            print(f"✅ Изменения в {day} применены")
        else:
            print(f"ℹ️ Изменений в {day} нет")
    
    async def run_daily_check(self):
        """Запускает ежедневную проверку голосований"""
        now = get_moscow_time()
        print(f"🕐 Запуск ежедневной проверки голосований - {now.strftime('%d.%m.%Y %H:%M')}")
        print(f"📅 День недели: {['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][now.weekday()]}")
        
        # Инициализация
        if not await self.initialize():
            print("❌ Не удалось инициализировать мониторинг")
            return False
        
        # Определяем активные опросы
        active_polls = self.get_active_polls_info()
        
        if not active_polls:
            print("ℹ️ Нет активных опросов для проверки")
            print("ℹ️ Проверка проводится:")
            print("   📅 Понедельник-среда: за вторник")
            print("   📅 Четверг-суббота: за пятницу")
            print("✅ Мониторинг завершен (нет активных опросов)")
            return True
        
        print(f"📋 Активные опросы: {list(active_polls.keys())}")
        for poll_key, poll_info in active_polls.items():
            print(f"   🏀 {poll_info['day']}: период {poll_info['period']}")
        
        # Ищем активный опрос тренировок в Telegram
        print("🔍 Поиск активного опроса тренировок в чате...")
        poll_id = await self.find_active_training_poll()
        
        if not poll_id:
            print("⚠️ Активный опрос тренировок не найден в чате")
            print("ℹ️ Это означает, что опрос тренировок еще не был создан")
            print("ℹ️ Ожидайте создания опроса в воскресенье")
            print("✅ Мониторинг завершен (нет активного опроса)")
            return True  # Не ошибка, просто нет активного опроса
        
        print(f"📊 Найден активный опрос: {poll_id}")
        
        # Обрабатываем каждый активный день
        for day_key, day_info in active_polls.items():
            day_name = day_info['day']
            await self.process_poll_changes(poll_id, day_name)
        
        print("✅ Ежедневная проверка завершена")
        return True


async def main():
    """Основная функция"""
    monitor = DailyPollMonitor()
    await monitor.run_daily_check()


if __name__ == "__main__":
    asyncio.run(main())