#!/usr/bin/env python3
"""
Модуль для ручного сбора данных о посещаемости тренировок
"""

import os
import asyncio
import datetime
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = int(os.getenv("ANNOUNCEMENTS_TOPIC_ID", "26"))

class ManualAttendanceCollector:
    """Коллектор для ручного сбора данных о посещаемости"""
    
    def __init__(self):
        self.bot = None
        self.attendance_data = {}
        self._init_bot()
    
    def _init_bot(self):
        """Инициализация бота"""
        try:
            if not BOT_TOKEN:
                print("❌ BOT_TOKEN не настроен")
                return
            
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Telegram Bot API инициализирован")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации бота: {e}")
    
    async def send_attendance_request(self, training_day: str):
        """Отправляет запрос на сбор данных о посещаемости"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            message_text = f"""
📊 СБОР ДАННЫХ О ПОСЕЩАЕМОСТИ

🏀 Тренировка: {training_day}

Пожалуйста, ответьте на этот опрос, если вы были на тренировке {training_day}:

✅ Был на тренировке
❌ Не был на тренировке

Данные будут использованы для статистики посещаемости.
            """.strip()
            
            # Создаем опрос для сбора данных
            poll_question = f"Вы были на тренировке {training_day}?"
            poll_options = ["✅ Был на тренировке", "❌ Не был на тренировке"]
            
            await self.bot.send_poll(
                chat_id=int(CHAT_ID),
                question=poll_question,
                options=poll_options,
                is_anonymous=False,  # Показываем имена участников
                allows_multiple_answers=False,
                explanation="Данные будут использованы для статистики посещаемости"
            )
            
            print(f"✅ Запрос на сбор данных за {training_day} отправлен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки запроса: {e}")
            return False
    
    async def create_attendance_summary(self, training_day: str, attendees: List[str], absentees: List[str]):
        """Создает сводку по посещаемости"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return False
        
        try:
            message_text = f"""
📊 СВОДКА ПОСЕЩАЕМОСТИ

🏀 Тренировка: {training_day}
📅 Дата: {datetime.datetime.now().strftime('%Y-%m-%d')}

✅ Присутствовали ({len(attendees)} человек):
{chr(10).join([f"   • {attendee}" for attendee in attendees]) if attendees else "   Нет данных"}

❌ Отсутствовали ({len(absentees)} человек):
{chr(10).join([f"   • {absentee}" for absentee in absentees]) if absentees else "   Нет данных"}

📈 Общая посещаемость: {len(attendees)} из {len(attendees) + len(absentees)} участников
            """.strip()
            
            await self.bot.send_message(
                chat_id=int(CHAT_ID),
                text=message_text,
                parse_mode='HTML'
            )
            
            print(f"✅ Сводка по посещаемости за {training_day} отправлена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки сводки: {e}")
            return False

# Глобальный экземпляр
attendance_collector = ManualAttendanceCollector()

async def test_manual_collection():
    """Тестирует ручной сбор данных"""
    print("🧪 Тестирование ручного сбора данных о посещаемости...")
    
    try:
        # Определяем, какой день тренировки нужно проверить
        now = datetime.datetime.now()
        weekday = now.weekday()
        
        if weekday == 2:  # Среда
            training_day = "Вторник"
        elif weekday == 5:  # Суббота
            training_day = "Пятница"
        else:
            print("⚠️ Сегодня не день сбора данных (среда или суббота)")
            return False
        
        print(f"📅 Сбор данных за {training_day}")
        
        # Отправляем запрос на сбор данных
        success = await attendance_collector.send_attendance_request(training_day)
        
        if success:
            print("✅ Запрос на сбор данных отправлен успешно")
            print("📋 Теперь участники могут голосовать в опросе")
            print("⏰ Через некоторое время можно будет собрать результаты")
        else:
            print("❌ Ошибка отправки запроса")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_manual_collection())
