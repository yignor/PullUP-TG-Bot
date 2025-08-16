#!/usr/bin/env python3
"""
Улучшенный модуль тренировок с поддержкой статистики по игрокам
"""

import os
import asyncio
import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Импортируем улучшенный обработчик (после определения переменных окружения)
from enhanced_poll_handler import enhanced_poll_handler


class EnhancedTrainingPollsManager:
    """Улучшенный менеджер опросов тренировок с поддержкой статистики по игрокам"""

    def __init__(self):
        self.spreadsheet = None
        self._init_google_sheets()

    def _init_google_sheets(self):
        """Инициализация Google Sheets"""
        try:
            if not GOOGLE_SHEETS_CREDENTIALS or not SPREADSHEET_ID:
                print("⚠️ GOOGLE_SHEETS_CREDENTIALS или SPREADSHEET_ID не настроены")
                return

            import gspread
            from google.oauth2.service_account import Credentials

            # Настройка аутентификации
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = Credentials.from_service_account_info(
                eval(GOOGLE_SHEETS_CREDENTIALS), scopes=scope
            )

            # Подключение к Google Sheets
            gc = gspread.authorize(credentials)
            self.spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            print(f"✅ Google Sheets подключен: {self.spreadsheet.title}")

        except Exception as e:
            print(f"❌ Ошибка подключения к Google Sheets: {e}")

    async def create_weekly_training_poll(self):
        """Создает опрос тренировок на неделю (каждое воскресенье в 9:00)"""
        try:
            from telegram import Bot

            if not BOT_TOKEN:
                print("❌ BOT_TOKEN не настроен")
                return None

            bot = Bot(token=BOT_TOKEN)

            question = "Тренировки на неделе"
            options = [
                "Вторник СШОР 19:00",
                "Среда 550 школа 19:00",
                "Пятница СШОР 20:30",
                "Нет",
                "Тренер"
            ]

            # Создаем НЕ анонимный опрос для получения имен участников
            poll = await bot.send_poll(
                chat_id=CHAT_ID,
                question=question,
                options=options,
                allows_multiple_answers=True,
                is_anonymous=False,  # Важно: НЕ анонимный опрос
                explanation="Выберите тренировки, на которые планируете прийти на этой неделе",
                message_thread_id=ANNOUNCEMENTS_TOPIC_ID
            )

            print(f"✅ Опрос тренировок создан: {poll.poll.question}")
            print(f"   ID опроса: {poll.poll.id}")
            print(f"   Анонимный: {poll.poll.is_anonymous}")
            return poll

        except Exception as e:
            print(f"❌ Ошибка создания опроса тренировок: {e}")
            return None

    def save_attendance_to_sheet(self, poll_date: str, attendance_stats: Dict[str, Any]):
        """Сохраняет данные о посещаемости в Google Sheets с именами участников"""
        try:
            if not self.spreadsheet:
                print("❌ Google Sheets не подключен")
                return False

            # Получаем или создаем лист для текущего месяца
            month_year = datetime.datetime.fromisoformat(poll_date).strftime("%Y-%m")
            sheet_name = f"Тренировки_{month_year}"

            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except Exception:
                # Создаем новый лист
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=100,
                    cols=10
                )
                # Добавляем заголовки
                headers = [
                    "Дата опроса", "День недели", "Тренировка",
                    "Участники", "Количество", "Уникальные участники"
                ]
                worksheet.update('A1:F1', [headers])

            # Подготавливаем данные для записи
            rows_to_add = []

            for day, data in attendance_stats.get('by_day', {}).items():
                participants = data.get('participants', [])
                unique_participants = list(set(participants))  # Убираем дубликаты

                row = [
                    poll_date,  # Дата опроса
                    day,        # День недели
                    f"{day} тренировка",  # Название тренировки
                    ", ".join(unique_participants),  # Список участников
                    len(unique_participants),        # Количество участников
                    len(unique_participants)         # Уникальные участники
                ]
                rows_to_add.append(row)

            if rows_to_add:
                # Добавляем данные в конец листа
                next_row = len(worksheet.get_all_values()) + 1
                worksheet.update(f'A{next_row}:F{next_row + len(rows_to_add) - 1}', rows_to_add)
                print(f"✅ Данные сохранены в лист '{sheet_name}'")
                return True

            return False

        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False

    def generate_monthly_player_statistics(self, month_year: str = None) -> Dict[str, Any]:
        """Генерирует месячную статистику по игрокам"""
        try:
            if not self.spreadsheet:
                print("❌ Google Sheets не подключен")
                return {"message": "Google Sheets не подключен"}

            # Определяем месяц для анализа
            if not month_year:
                month_year = datetime.datetime.now().strftime("%Y-%m")

            sheet_name = f"Тренировки_{month_year}"

            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except Exception:
                return {"message": f"Данные за {month_year} отсутствуют"}

            # Получаем все данные
            data = worksheet.get_all_values()

            if len(data) <= 1:  # Только заголовки
                return {"message": f"Данные за {month_year} отсутствуют"}

            # Анализируем данные
            stats = {
                "month": month_year,
                "total_trainings": 0,
                "total_participants": 0,
                "by_day": {},
                "by_player": {},
                "most_active": [],
                "least_active": [],
                "player_attendance_details": {}
            }

            # Парсим данные (начиная со второй строки, пропуская заголовки)
            for row in data[1:]:
                if len(row) >= 6:
                    poll_date, day, training, participants, count, unique_count = row[:6]

                    if unique_count and unique_count.isdigit():
                        count = int(unique_count)
                        stats["total_trainings"] += 1
                        stats["total_participants"] += count

                        # Статистика по дням
                        if day not in stats["by_day"]:
                            stats["by_day"][day] = {"count": 0, "participants": 0, "unique_participants": set()}
                        stats["by_day"][day]["count"] += 1
                        stats["by_day"][day]["participants"] += count

                        # Статистика по игрокам
                        if participants:
                            for player in participants.split(", "):
                                player = player.strip()
                                if player and player != "Участник":
                                    if player not in stats["by_player"]:
                                        stats["by_player"][player] = {
                                            "total_attendance": 0,
                                            "days_attended": set(),
                                            "trainings_attended": []
                                        }

                                    stats["by_player"][player]["total_attendance"] += 1
                                    stats["by_player"][player]["days_attended"].add(day)
                                    stats["by_player"][player]["trainings_attended"].append({
                                        "date": poll_date,
                                        "day": day,
                                        "training": training
                                    })

                                    stats["by_day"][day]["unique_participants"].add(player)

            # Конвертируем множества в списки для JSON
            for day_data in stats["by_day"].values():
                day_data["unique_participants"] = list(day_data["unique_participants"])

            for player_data in stats["by_player"].values():
                player_data["days_attended"] = list(player_data["days_attended"])

            # Находим самых активных и неактивных
            if stats["by_player"]:
                sorted_players = sorted(
                    stats["by_player"].items(),
                    key=lambda x: x[1]["total_attendance"],
                    reverse=True
                )
                stats["most_active"] = sorted_players[:5]  # Топ-5
                stats["least_active"] = sorted_players[-5:]  # Последние 5

            return stats

        except Exception as e:
            print(f"❌ Ошибка генерации статистики: {e}")
            return {"message": f"Ошибка генерации статистики: {e}"}

    async def send_monthly_player_report(self, stats: Dict[str, Any]):
        """Отправляет месячный отчет по игрокам в чат"""
        try:
            from telegram import Bot

            if not BOT_TOKEN:
                print("❌ BOT_TOKEN не настроен")
                return

            bot = Bot(token=BOT_TOKEN)

            if not stats or "message" in stats:
                message = f"📊 Месячный отчет по тренировкам\n\n❌ {stats.get('message', 'Данные отсутствуют')}"
            else:
                message = f"📊 МЕСЯЧНЫЙ ОТЧЕТ ПО ТРЕНИРОВКАМ ({stats['month']})\n\n"
                message += f"🏀 Всего тренировок: {stats['total_trainings']}\n"
                message += f"👥 Уникальных участников: {len(stats['by_player'])}\n"
                message += f"📈 Общее количество посещений: {stats['total_participants']}\n\n"

                message += "📅 Статистика по дням недели:\n"
                for day, data in stats['by_day'].items():
                    unique_count = len(data['unique_participants'])
                    message += f"  {day}: {data['count']} тренировок, {unique_count} уникальных участников\n"

                if stats['most_active']:
                    message += "\n🏆 ТОП-5 САМЫХ АКТИВНЫХ ИГРОКОВ:\n"
                    for i, (player, data) in enumerate(stats['most_active'], 1):
                        days_str = ", ".join(data['days_attended'])
                        message += f"  {i}. {player}: {data['total_attendance']} тренировок ({days_str})\n"

                if stats['least_active']:
                    message += "\n📉 МЕНЕЕ АКТИВНЫЕ ИГРОКИ:\n"
                    for i, (player, data) in enumerate(stats['least_active'], 1):
                        days_str = ", ".join(data['days_attended']) if data['days_attended'] else "нет"
                        message += f"  {i}. {player}: {data['total_attendance']} тренировок ({days_str})\n"

                message += "\n📋 ДЕТАЛЬНАЯ СТАТИСТИКА ПО ИГРОКАМ:\n"
                for player, data in stats['by_player'].items():
                    days_str = ", ".join(data['days_attended'])
                    message += f"  {player}: {data['total_attendance']} тренировок ({days_str})\n"

            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                message_thread_id=ANNOUNCEMENTS_TOPIC_ID
            )
            print("✅ Месячный отчет по игрокам отправлен")

        except Exception as e:
            print(f"❌ Ошибка отправки отчета: {e}")


# Глобальный экземпляр
enhanced_training_manager = EnhancedTrainingPollsManager()


async def collect_enhanced_attendance_data():
    """Собирает данные о посещаемости с именами участников"""
    try:
        # Запускаем клиент
        if not await enhanced_poll_handler.start_client():
            print("❌ Не удалось запустить Telegram Client")
            return None

        # Получаем последний опрос тренировок, созданный в воскресенье
        latest_poll = await enhanced_poll_handler.get_latest_sunday_training_poll()

        if not latest_poll:
            print("📊 Последний опрос тренировок не найден")
            await enhanced_poll_handler.close_client()
            return None

        # Генерируем статистику посещаемости
        attendance_stats = enhanced_poll_handler.generate_attendance_statistics(latest_poll)

        # Обрабатываем опрос
        poll_date = datetime.datetime.fromisoformat(latest_poll['date'].replace('Z', '+00:00')).date()
        date_str = poll_date.strftime("%Y-%m-%d")

        print(f"📅 Обрабатываю опрос от {date_str}:")
        for day, data in attendance_stats.get('by_day', {}).items():
            if data['participants']:
                print(f"   {day}: {data['count']} участников")

        await enhanced_poll_handler.close_client()
        return {
            'poll_date': date_str,
            'stats': attendance_stats
        }

    except ImportError:
        print("⚠️ Модуль enhanced_poll_handler не найден")
        return None
    except Exception as e:
        print(f"❌ Ошибка сбора данных о посещаемости: {e}")
        return None


async def should_create_weekly_poll() -> bool:
    """Проверяет, нужно ли создать опрос на неделю (воскресенье 9:00)"""
    now = datetime.datetime.now()
    return now.weekday() == 6 and now.hour == 9 and now.minute < 30


async def should_collect_attendance() -> bool:
    """Проверяет, нужно ли собрать данные о посещаемости (среда/суббота 9:00)"""
    now = datetime.datetime.now()
    return (now.weekday() in [2, 5]) and now.hour == 9 and now.minute < 30


async def should_generate_monthly_report() -> bool:
    """Проверяет, нужно ли сгенерировать месячный отчет (последний день месяца 9:00)"""
    now = datetime.datetime.now()
    last_day = (now.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    return now.day == last_day.day and now.hour == 9 and now.minute < 30


async def main_enhanced_training_polls():
    """Основная функция для управления улучшенными опросами тренировок"""
    try:
        now = datetime.datetime.now()
        print(f"🏀 Проверка улучшенных опросов тренировок в {now.strftime('%Y-%m-%d %H:%M')}...")

        # Создание опроса на неделю (воскресенье 9:00)
        if await should_create_weekly_poll():
            print("📊 Создаю опрос тренировок на неделю...")
            await enhanced_training_manager.create_weekly_training_poll()

        # Сбор данных о посещаемости (среда/суббота 9:00)
        if await should_collect_attendance():
            print("📋 Собираю данные о посещаемости...")
            attendance_data = await collect_enhanced_attendance_data()

            if attendance_data:
                # Сохраняем данные в Google Sheets
                success = enhanced_training_manager.save_attendance_to_sheet(
                    attendance_data['poll_date'],
                    attendance_data['stats']
                )
                if success:
                    print(f"✅ Данные за {attendance_data['poll_date']} сохранены")
                else:
                    print(f"❌ Ошибка сохранения данных за {attendance_data['poll_date']}")
            else:
                print("⚠️ Данные о посещаемости не найдены")

        # Генерация месячного отчета (последний день месяца 9:00)
        if await should_generate_monthly_report():
            print("📊 Генерирую месячный отчет по игрокам...")
            stats = enhanced_training_manager.generate_monthly_player_statistics()
            await enhanced_training_manager.send_monthly_player_report(stats)

        print("✅ Проверка улучшенных опросов тренировок завершена")

    except Exception as e:
        print(f"❌ Ошибка в main_enhanced_training_polls: {e}")


if __name__ == "__main__":
    asyncio.run(main_enhanced_training_polls())
