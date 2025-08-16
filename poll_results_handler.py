#!/usr/bin/env python3
"""
Модуль для получения результатов опросов Telegram
Использует Telegram Client API для доступа к результатам опросов
"""

import os
import asyncio
import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")

class PollResultsHandler:
    """Обработчик результатов опросов"""
    
    def __init__(self):
        self.client = None
        self._init_telegram_client()
    
    def _init_telegram_client(self):
        """Инициализация Telegram Client API"""
        try:
            if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE]):
                print("⚠️ Переменные для Telegram Client API не настроены")
                print("   Нужно: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
                return
            
            # Импортируем только при необходимости
            from telethon import TelegramClient
            
            self.client = TelegramClient(
                'bot_session',
                int(TELEGRAM_API_ID),
                TELEGRAM_API_HASH
            )
            print("✅ Telegram Client API инициализирован")
            
        except ImportError:
            print("⚠️ telethon не установлен. Установите: pip install telethon")
        except Exception as e:
            print(f"❌ Ошибка инициализации Telegram Client: {e}")
    
    async def start_client(self):
        """Запускает клиент"""
        if not self.client:
            return False
        
        try:
            await self.client.start(phone=TELEGRAM_PHONE)
            print("✅ Telegram Client подключен")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения клиента: {e}")
            return False
    
    async def get_poll_results(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Получает результаты опроса по ID сообщения"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return None
        
        try:
            # Получаем сообщение с опросом
            message = await self.client.get_messages(
                int(CHAT_ID),
                ids=message_id
            )
            
            if not message or not message.poll:
                print(f"❌ Сообщение {message_id} не содержит опрос")
                return None
            
            poll = message.poll
            
            # Собираем результаты
            results = {
                'question': poll.question,
                'options': [],
                'total_voters': poll.total_voters,
                'is_anonymous': poll.anonymous,
                'allows_multiple_answers': poll.multiple_choice,
                'message_id': message_id,
                'date': message.date.isoformat()
            }
            
            # Обрабатываем варианты ответов
            for option in poll.answers:
                option_data = {
                    'text': option.text,
                    'voters': option.voters,
                    'option_id': option.option
                }
                results['options'].append(option_data)
            
            print(f"✅ Получены результаты опроса: {poll.question}")
            return results
            
        except Exception as e:
            print(f"❌ Ошибка получения результатов опроса: {e}")
            return None
    
    async def get_recent_polls(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получает все опросы за последние N часов"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return []
        
        try:
            # Вычисляем время начала поиска
            since = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            # Получаем сообщения с опросами
            messages = await self.client.get_messages(
                int(CHAT_ID),
                search='poll',
                limit=100,
                offset_date=since
            )
            
            polls = []
            for message in messages:
                if message.poll:
                    poll_data = await self.get_poll_results(message.id)
                    if poll_data:
                        polls.append(poll_data)
            
            print(f"✅ Найдено {len(polls)} опросов за последние {hours} часов")
            return polls
            
        except Exception as e:
            print(f"❌ Ошибка поиска опросов: {e}")
            return []
    
    async def get_latest_sunday_training_poll(self) -> Optional[Dict[str, Any]]:
        """Получает последний опрос тренировок, созданный в воскресенье"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return None
        
        try:
            # Ищем опросы с вопросом о тренировках за последние 7 дней
            since = datetime.datetime.now() - datetime.timedelta(days=7)
            
            messages = await self.client.get_messages(
                int(CHAT_ID),
                search='Тренировки на неделе',
                limit=50,
                offset_date=since
            )
            
            # Фильтруем опросы, созданные в воскресенье
            sunday_polls = []
            for message in messages:
                if message.poll and "тренировки" in message.poll.question.lower():
                    # Проверяем, что сообщение создано в воскресенье
                    message_date = message.date
                    if message_date.weekday() == 6:  # 6 = воскресенье
                        poll_data = await self.get_poll_results(message.id)
                        if poll_data:
                            sunday_polls.append(poll_data)
            
            if sunday_polls:
                # Берем самый последний опрос (первый в списке, так как сообщения отсортированы по дате)
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

    async def get_training_poll_results(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Получает результаты опросов тренировок за последние N дней"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return []
        
        try:
            # Ищем опросы с вопросом о тренировках
            since = datetime.datetime.now() - datetime.timedelta(days=days_back)
            
            messages = await self.client.get_messages(
                int(CHAT_ID),
                search='Тренировки на неделе',
                limit=50,
                offset_date=since
            )
            
            training_polls = []
            for message in messages:
                if message.poll and "тренировки" in message.poll.question.lower():
                    poll_data = await self.get_poll_results(message.id)
                    if poll_data:
                        training_polls.append(poll_data)
            
            print(f"✅ Найдено {len(training_polls)} опросов тренировок")
            return training_polls
            
        except Exception as e:
            print(f"❌ Ошибка поиска опросов тренировок: {e}")
            return []
    
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
            for option in poll_results.get('options', []):
                option_text = option.get('text', '').lower()
                voters = option.get('voters', 0)
                
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
                
                if category and voters > 0:
                    # Здесь нужно будет получить список проголосовавших
                    # К сожалению, Telegram не предоставляет эту информацию для анонимных опросов
                    # Поэтому используем количество голосов как индикатор
                    attendees[category].append(f"Участник (голосов: {voters})")
            
            return attendees
            
        except Exception as e:
            print(f"❌ Ошибка парсинга голосов: {e}")
            return attendees
    
    async def close_client(self):
        """Закрывает клиент"""
        if self.client:
            await self.client.disconnect()
            print("✅ Telegram Client отключен")

# Глобальный экземпляр
poll_handler = PollResultsHandler()

async def test_poll_results():
    """Тестирует получение результатов опросов"""
    print("🧪 Тестирование получения результатов опросов...")
    
    try:
        # Запускаем клиент
        if not await poll_handler.start_client():
            print("❌ Не удалось запустить клиент")
            return False
        
        # Получаем последние опросы
        recent_polls = await poll_handler.get_recent_polls(hours=24)
        
        if recent_polls:
            print(f"\n📊 Найдено {len(recent_polls)} опросов:")
            for i, poll in enumerate(recent_polls, 1):
                print(f"\n{i}. {poll['question']}")
                print(f"   Всего голосов: {poll['total_voters']}")
                for option in poll['options']:
                    print(f"   - {option['text']}: {option['voters']} голосов")
        else:
            print("📊 Опросы не найдены")
        
        # Получаем опросы тренировок
        training_polls = await poll_handler.get_training_poll_results(days_back=7)
        
        if training_polls:
            print(f"\n🏋️‍♂️ Найдено {len(training_polls)} опросов тренировок:")
            for poll in training_polls:
                attendees = poll_handler.parse_training_votes(poll)
                print(f"\n📅 Опрос от {poll['date']}:")
                for day, users in attendees.items():
                    if users:
                        print(f"   {day}: {len(users)} участников")
        
        await poll_handler.close_client()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_poll_results())
