#!/usr/bin/env python3
"""
Модуль для получения результатов опросов через Telegram Bot API
"""

import os
import asyncio
import datetime
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = int(os.getenv("ANNOUNCEMENTS_TOPIC_ID", "26"))

class BotPollResultsHandler:
    """Обработчик результатов опросов через Bot API"""
    
    def __init__(self):
        self.bot = None
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
    
    async def get_chat_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает историю сообщений из чата"""
        if not self.bot or not CHAT_ID:
            print("❌ Бот или CHAT_ID не настроены")
            return []
        
        try:
            messages = []
            # Получаем сообщения по одному, начиная с последнего
            offset = 0
            
            while len(messages) < limit:
                try:
                    # Получаем сообщения с помощью getUpdates или прямого запроса
                    # К сожалению, Bot API не предоставляет прямой доступ к истории сообщений
                    # Поэтому используем альтернативный подход
                    
                    # Для получения результатов опросов нужно использовать webhook или polling
                    # Но это сложно для простого тестирования
                    
                    print("⚠️ Bot API не предоставляет прямой доступ к истории сообщений")
                    print("   Для получения результатов опросов нужен Telegram Client API")
                    break
                    
                except Exception as e:
                    print(f"❌ Ошибка получения сообщений: {e}")
                    break
            
            print(f"✅ Найдено {len(messages)} опросов в истории")
            return messages
            
        except TelegramError as e:
            print(f"❌ Ошибка получения истории: {e}")
            return []
    
    async def get_training_polls(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Получает опросы тренировок за последние N дней"""
        try:
            all_polls = await self.get_chat_history(limit=200)
            
            # Фильтруем опросы тренировок
            training_polls = []
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
            
            for poll_data in all_polls:
                poll_date = datetime.datetime.fromisoformat(poll_data['date'].replace('Z', '+00:00'))
                question = poll_data['poll']['question'].lower()
                
                if poll_date >= cutoff_date and 'тренировки' in question:
                    training_polls.append(poll_data)
            
            print(f"✅ Найдено {len(training_polls)} опросов тренировок за последние {days_back} дней")
            return training_polls
            
        except Exception as e:
            print(f"❌ Ошибка поиска опросов тренировок: {e}")
            return []
    
    async def get_latest_sunday_training_poll(self) -> Optional[Dict[str, Any]]:
        """Получает последний опрос тренировок, созданный в воскресенье"""
        try:
            training_polls = await self.get_training_polls(days_back=7)
            
            # Ищем опросы, созданные в воскресенье
            sunday_polls = []
            for poll_data in training_polls:
                poll_date = datetime.datetime.fromisoformat(poll_data['date'].replace('Z', '+00:00'))
                if poll_date.weekday() == 6:  # 6 = воскресенье
                    sunday_polls.append(poll_data)
            
            if sunday_polls:
                # Берем самый последний опрос
                latest_poll = sunday_polls[0]
                poll_date = datetime.datetime.fromisoformat(latest_poll['date'].replace('Z', '+00:00'))
                print(f"✅ Найден последний опрос тренировок от {poll_date.strftime('%Y-%m-%d %H:%M')}")
                return latest_poll
            else:
                print("⚠️ Опросы тренировок за последнее воскресенье не найдены")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка поиска последнего опроса тренировок: {e}")
            return None
    
    def parse_training_votes(self, poll_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Парсит голоса за тренировки из результатов опроса"""
        attendees = {
            "Вторник": [],
            "Пятница": [],
            "Тренер": [],
            "Нет": []
        }
        
        try:
            # Обрабатываем каждый вариант ответа
            for option in poll_results['poll']['options']:
                option_text = option['text'].lower()
                voter_count = option['voter_count']
                
                # Определяем категорию по тексту
                category = None
                if 'вторник' in option_text:
                    category = "Вторник"
                elif 'пятница' in option_text:
                    category = "Пятница"
                elif 'тренер' in option_text:
                    category = "Тренер"
                elif 'нет' in option_text:
                    category = "Нет"
                
                if category and voter_count > 0:
                    attendees[category].append(f"Участник (голосов: {voter_count})")
            
            return attendees
            
        except Exception as e:
            print(f"❌ Ошибка парсинга голосов: {e}")
            return attendees

# Глобальный экземпляр
bot_poll_handler = BotPollResultsHandler()

async def test_bot_poll_results():
    """Тестирует получение результатов опросов через Bot API"""
    print("🧪 Тестирование получения результатов опросов через Bot API...")
    
    try:
        # Получаем последние опросы
        recent_polls = await bot_poll_handler.get_chat_history(limit=20)
        
        if recent_polls:
            print(f"\n📊 Найдено {len(recent_polls)} опросов:")
            for i, poll in enumerate(recent_polls, 1):
                print(f"\n{i}. {poll['poll']['question']}")
                print(f"   Всего голосов: {poll['poll']['total_voter_count']}")
                for option in poll['poll']['options']:
                    print(f"   - {option['text']}: {option['voter_count']} голосов")
        else:
            print("📊 Опросы не найдены")
        
        # Получаем опросы тренировок
        training_polls = await bot_poll_handler.get_training_polls(days_back=7)
        
        if training_polls:
            print(f"\n🏋️‍♂️ Найдено {len(training_polls)} опросов тренировок:")
            for poll in training_polls:
                attendees = bot_poll_handler.parse_training_votes(poll)
                print(f"\n📅 Опрос от {poll['date']}:")
                for day, users in attendees.items():
                    if users:
                        print(f"   {day}: {len(users)} участников")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot_poll_results())
