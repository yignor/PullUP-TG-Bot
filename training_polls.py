#!/usr/bin/env python3
"""
Модуль для управления опросами тренировок с интеграцией Google Sheets
"""

import os
import asyncio
import datetime
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Bot, Poll
import gspread
from google.oauth2.service_account import Credentials

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")  # ID топика "АНОНСЫ ТРЕНИРОВОК"
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")  # JSON credentials
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # ID Google таблицы

# Инициализация бота
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

# Настройки Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Варианты ответов для опроса тренировок
TRAINING_OPTIONS = [
    "🏀 Вторник 19:00",
    "🏀 Пятница 20:30",
    "👨‍🏫 Тренер",
    "❌ Нет"
]

# Дни недели для тренировок
TRAINING_DAYS = ["Вторник", "Пятница"]

class TrainingPollsManager:
    """Менеджер опросов тренировок"""
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self._init_google_sheets()
    
    def _init_google_sheets(self):
        """Инициализация Google Sheets"""
        try:
            if not GOOGLE_SHEETS_CREDENTIALS:
                print("⚠️ GOOGLE_SHEETS_CREDENTIALS не настроен")
                return
            
            # Парсим JSON credentials
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
        """Создает опрос тренировок на неделю (каждое воскресенье в 9:00)"""
        try:
            if not bot:
                print("❌ Бот не инициализирован")
                return None
            
            question = "🏀 Тренировки на неделе СШОР ВО"
            
            # Создаем опрос с множественным выбором
            poll = await bot.send_poll(
                chat_id=CHAT_ID,
                question=question,
                options=TRAINING_OPTIONS,
                allows_multiple_answers=True,
                is_anonymous=False,  # Открытый опрос
                explanation="Выберите тренировки, на которые планируете прийти на этой неделе",
                message_thread_id=ANNOUNCEMENTS_TOPIC_ID  # Отправляем в топик "АНОНСЫ ТРЕНИРОВОК"
            )
            
            print(f"✅ Опрос тренировок создан: {poll.poll.question}")
            return poll
            
        except Exception as e:
            print(f"❌ Ошибка создания опроса тренировок: {e}")
            return None
    
    async def get_poll_results(self, poll_id: str) -> Dict[str, List[str]]:
        """Получает результаты опроса по ID"""
        try:
            # Получаем информацию об опросе
            poll_info = await bot.get_chat(chat_id=CHAT_ID)
            
            # Здесь нужно будет реализовать получение результатов опросов
            # К сожалению, Telegram Bot API не предоставляет прямой доступ к результатам опросов
            # Нужно будет использовать Telegram Client API или сохранять результаты вручную
            
            print(f"⚠️ Получение результатов опроса {poll_id} требует дополнительной реализации")
            return {}
            
        except Exception as e:
            print(f"❌ Ошибка получения результатов опроса: {e}")
            return {}
    
    def save_attendance_to_sheet(self, date: str, attendees: Dict[str, List[str]]):
        """Сохраняет данные о посещаемости в Google таблицу"""
        try:
            if not self.spreadsheet:
                print("❌ Google таблица не подключена")
                return False
            
            # Получаем или создаем лист для текущего месяца
            month_year = datetime.datetime.now().strftime("%Y-%m")
            try:
                worksheet = self.spreadsheet.worksheet(month_year)
            except:
                # Создаем новый лист
                worksheet = self.spreadsheet.add_worksheet(title=month_year, rows=100, cols=10)
                
                # Заголовки
                headers = ["Дата", "День недели", "Тренировка", "Участники", "Количество"]
                worksheet.update('A1:E1', [headers])
            
            # Добавляем данные
            row_data = []
            for day, users in attendees.items():
                if users:  # Если есть участники
                    row_data.append([
                        date,
                        day,
                        day,  # Название тренировки
                        ", ".join(users),
                        len(users)
                    ])
            
            if row_data:
                # Находим следующую пустую строку
                next_row = len(worksheet.get_all_values()) + 1
                worksheet.update(f'A{next_row}:E{next_row + len(row_data) - 1}', row_data)
                print(f"✅ Данные о посещаемости сохранены: {len(row_data)} записей")
                return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в Google таблицу: {e}")
            return False
    
    def generate_monthly_statistics(self) -> Dict[str, Any]:
        """Генерирует статистику посещений за месяц"""
        try:
            if not self.spreadsheet:
                print("❌ Google таблица не подключена")
                return {}
            
            month_year = datetime.datetime.now().strftime("%Y-%m")
            try:
                worksheet = self.spreadsheet.worksheet(month_year)
            except:
                print(f"❌ Лист {month_year} не найден")
                return {}
            
            # Получаем все данные
            data = worksheet.get_all_values()
            if len(data) <= 1:  # Только заголовки
                return {"message": "Данные за месяц отсутствуют"}
            
            # Анализируем данные
            stats = {
                "total_trainings": 0,
                "total_participants": 0,
                "by_day": {},
                "by_person": {},
                "most_active": [],
                "least_active": []
            }
            
            # Парсим данные (начиная со второй строки, пропуская заголовки)
            for row in data[1:]:
                if len(row) >= 5:
                    date, day, training, participants, count = row[:5]
                    
                    if count and count.isdigit():
                        count = int(count)
                        stats["total_trainings"] += 1
                        stats["total_participants"] += count
                        
                        # Статистика по дням
                        if day not in stats["by_day"]:
                            stats["by_day"][day] = {"count": 0, "participants": 0}
                        stats["by_day"][day]["count"] += 1
                        stats["by_day"][day]["participants"] += count
                        
                        # Статистика по участникам
                        if participants:
                            for person in participants.split(", "):
                                person = person.strip()
                                if person:
                                    if person not in stats["by_person"]:
                                        stats["by_person"][person] = 0
                                    stats["by_person"][person] += 1
            
            # Находим самых активных и неактивных
            if stats["by_person"]:
                sorted_participants = sorted(stats["by_person"].items(), key=lambda x: x[1], reverse=True)
                stats["most_active"] = sorted_participants[:3]  # Топ-3
                stats["least_active"] = sorted_participants[-3:]  # Последние 3
            
            return stats
            
        except Exception as e:
            print(f"❌ Ошибка генерации статистики: {e}")
            return {}
    
    async def send_monthly_report(self, stats: Dict[str, Any]):
        """Отправляет месячный отчет в чат"""
        try:
            if not stats or "message" in stats:
                message = "📊 Месячный отчет по тренировкам\n\n❌ Данные за месяц отсутствуют"
            else:
                message = "📊 Месячный отчет по тренировкам\n\n"
                message += f"🏀 Всего тренировок: {stats['total_trainings']}\n"
                message += f"👥 Общее количество участников: {stats['total_participants']}\n\n"
                
                message += "📅 По дням недели:\n"
                for day, data in stats['by_day'].items():
                    message += f"  {day}: {data['count']} тренировок, {data['participants']} участников\n"
                
                if stats['most_active']:
                    message += "\n🏆 Самые активные участники:\n"
                    for person, count in stats['most_active']:
                        message += f"  {person}: {count} тренировок\n"
                
                if stats['least_active']:
                    message += "\n📉 Менее активные участники:\n"
                    for person, count in stats['least_active']:
                        message += f"  {person}: {count} тренировок\n"
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                message_thread_id=ANNOUNCEMENTS_TOPIC_ID
            )
            print("✅ Месячный отчет отправлен")
            
        except Exception as e:
            print(f"❌ Ошибка отправки отчета: {e}")

# Глобальный экземпляр менеджера
training_manager = TrainingPollsManager()

async def should_create_weekly_poll() -> bool:
    """Проверяет, нужно ли создать опрос на неделю (воскресенье 9:00)"""
    now = datetime.datetime.now()
    return now.weekday() == 6 and now.hour == 9 and now.minute < 30  # Воскресенье 9:00

async def should_collect_attendance() -> bool:
    """Проверяет, нужно ли собрать данные о посещаемости (среда/суббота 9:00)"""
    now = datetime.datetime.now()
    return (now.weekday() in [2, 5]) and now.hour == 9 and now.minute < 30  # Среда/суббота 9:00

def get_target_training_day() -> str:
    """Определяет, какую тренировку нужно проверить в зависимости от дня недели"""
    now = datetime.datetime.now()
    weekday = now.weekday()
    
    if weekday == 2:  # Среда
        return "Вторник"  # Проверяем результат за Вторник
    elif weekday == 5:  # Суббота
        return "Пятница"  # Проверяем результат за Пятницу
    else:
        return None

async def collect_attendance_data():
    """Собирает данные о посещаемости из последнего опроса тренировок"""
    try:
        # Определяем, какую тренировку проверяем
        target_day = get_target_training_day()
        if not target_day:
            print("❌ Неверный день для сбора данных")
            return None
        
        print(f"📅 Проверяю результаты за {target_day}...")
        
        # Импортируем обработчик результатов
        from poll_results_handler import poll_handler
        
        # Запускаем клиент
        if not await poll_handler.start_client():
            print("❌ Не удалось запустить Telegram Client")
            return None
        
        # Получаем последний опрос тренировок, созданный в воскресенье
        latest_poll = await poll_handler.get_latest_sunday_training_poll()
        
        if not latest_poll:
            print("📊 Последний опрос тренировок не найден")
            await poll_handler.close_client()
            return None
        
        # Обрабатываем опрос
        poll_date = datetime.datetime.fromisoformat(latest_poll['date'].replace('Z', '+00:00')).date()
        all_attendees = poll_handler.parse_training_votes(latest_poll)
        
        # Фильтруем данные только для нужного дня
        filtered_attendees = {}
        if target_day in all_attendees:
            filtered_attendees[target_day] = all_attendees[target_day]
            print(f"✅ Найдены участники для {target_day}: {len(all_attendees[target_day])} человек")
        else:
            print(f"⚠️ Участники для {target_day} не найдены")
        
        # Сохраняем данные по дате создания опроса и дню тренировки
        date_str = poll_date.strftime("%Y-%m-%d")
        result = {f"{date_str}_{target_day}": filtered_attendees}
        
        print(f"📅 Обрабатываю опрос от {date_str} для {target_day}:")
        if filtered_attendees and target_day in filtered_attendees:
            users = filtered_attendees[target_day]
            print(f"   {target_day}: {len(users)} участников")
        else:
            print(f"   {target_day}: 0 участников")
        
        await poll_handler.close_client()
        return result
        
    except ImportError:
        print("⚠️ Модуль poll_results_handler не найден")
        return None
    except Exception as e:
        print(f"❌ Ошибка сбора данных о посещаемости: {e}")
        return None

async def should_generate_monthly_report() -> bool:
    """Проверяет, нужно ли сгенерировать месячный отчет (последний день месяца 9:00)"""
    now = datetime.datetime.now()
    last_day = (now.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    return now.day == last_day.day and now.hour == 9 and now.minute < 30

async def main_training_polls():
    """Основная функция для управления опросами тренировок"""
    try:
        now = datetime.datetime.now()
        print(f"🏀 Проверка опросов тренировок в {now.strftime('%Y-%m-%d %H:%M')}...")
        
        # Создание опроса на неделю (воскресенье 9:00)
        if await should_create_weekly_poll():
            print("📊 Создаю опрос тренировок на неделю...")
            await training_manager.create_weekly_training_poll()
        
        # Сбор данных о посещаемости (среда/суббота 9:00)
        if await should_collect_attendance():
            print("📋 Собираю данные о посещаемости...")
            attendance_data = await collect_attendance_data()
            
            if attendance_data:
                # Сохраняем данные в Google Sheets
                for date_key, attendees in attendance_data.items():
                    # date_key имеет формат "YYYY-MM-DD_ДеньНедели"
                    training_manager.save_attendance_to_sheet(date_key, attendees)
                    print(f"✅ Данные за {date_key} сохранены")
            else:
                print("⚠️ Данные о посещаемости не найдены")
        
        # Генерация месячного отчета (последний день месяца 9:00)
        if await should_generate_monthly_report():
            print("📊 Генерирую месячный отчет...")
            stats = training_manager.generate_monthly_statistics()
            await training_manager.send_monthly_report(stats)
        
        print("✅ Проверка опросов тренировок завершена")
        
    except Exception as e:
        print(f"❌ Ошибка в main_training_polls: {e}")

if __name__ == "__main__":
    asyncio.run(main_training_polls())
