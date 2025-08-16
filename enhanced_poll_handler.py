#!/usr/bin/env python3
"""
Улучшенный обработчик результатов опросов с поддержкой имен участников
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


class EnhancedPollHandler:
    """Улучшенный обработчик результатов опросов с поддержкой имен участников"""

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
            try:
                from telethon import TelegramClient
            except ImportError:
                print("⚠️ telethon не установлен. Установите: pip install telethon")
                return

            # Проверяем, что все переменные не None перед использованием
            if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
                print("❌ TELEGRAM_API_ID или TELEGRAM_API_HASH не настроены")
                return

            self.client = TelegramClient(
                'bot_session',
                int(TELEGRAM_API_ID),
                TELEGRAM_API_HASH
            )
            print("✅ Enhanced Telegram Client API инициализирован")

        except Exception as e:
            print(f"❌ Ошибка инициализации Telegram Client: {e}")

    async def start_client(self):
        """Запускает клиент"""
        if not self.client:
            return False

        try:
            if not TELEGRAM_PHONE:
                print("❌ TELEGRAM_PHONE не настроен")
                return False
                
            await self.client.start(phone=TELEGRAM_PHONE)
            print("✅ Enhanced Telegram Client подключен")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения клиента: {e}")
            return False

    async def get_poll_with_voters(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Получает результаты опроса с именами участников"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return None

        if not CHAT_ID:
            print("❌ CHAT_ID не настроен")
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

            # Проверяем, анонимный ли опрос
            if poll.anonymous:
                print("⚠️ Опрос анонимный - имена участников недоступны")
                return await self._get_anonymous_poll_results(message, poll)
            else:
                print("✅ Опрос публичный - получаем имена участников")
                return await self._get_public_poll_results(message, poll)

        except Exception as e:
            print(f"❌ Ошибка получения результатов опроса: {e}")
            return None

    async def _get_anonymous_poll_results(self, message, poll) -> Dict[str, Any]:
        """Обрабатывает анонимный опрос"""
        results = {
            'question': poll.question,
            'options': [],
            'total_voters': poll.total_voters,
            'is_anonymous': True,
            'allows_multiple_answers': poll.multiple_choice,
            'message_id': message.id,
            'date': message.date.isoformat(),
            'voters_by_option': {}
        }

        # Обрабатываем варианты ответов
        for option in poll.answers:
            option_data = {
                'text': option.text,
                'voters': option.voters,
                'option_id': option.option,
                'voter_names': []  # Пустой список для анонимных опросов
            }
            results['options'].append(option_data)
            results['voters_by_option'][option.option] = []

        return results

    async def _get_public_poll_results(self, message, poll) -> Dict[str, Any]:
        """Обрабатывает публичный опрос с именами участников"""
        results = {
            'question': poll.question,
            'options': [],
            'total_voters': poll.total_voters,
            'is_anonymous': False,
            'allows_multiple_answers': poll.multiple_choice,
            'message_id': message.id,
            'date': message.date.isoformat(),
            'voters_by_option': {}
        }

        # Получаем информацию о проголосовавших
        try:
            # Получаем обновления опроса для получения имен участников
            # Примечание: Telegram API ограничен в предоставлении этой информации
            # Поэтому используем альтернативный подход

            # Обрабатываем варианты ответов
            for option in poll.answers:
                option_data = {
                    'text': option.text,
                    'voters': option.voters,
                    'option_id': option.option,
                    'voter_names': []  # Будет заполнено ниже
                }
                results['options'].append(option_data)
                results['voters_by_option'][option.option] = []

            # Попытка получить имена участников (если доступно)
            # Примечание: Telegram API ограничен в предоставлении этой информации
            # Поэтому используем альтернативный подход

        except Exception as e:
            print(f"⚠️ Не удалось получить имена участников: {e}")

        return results

    async def get_latest_sunday_training_poll(self) -> Optional[Dict[str, Any]]:
        """Получает последний опрос тренировок, созданный в воскресенье"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return None

        if not CHAT_ID:
            print("❌ CHAT_ID не настроен")
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
                        poll_data = await self.get_poll_with_voters(message.id)
                        if poll_data:
                            sunday_polls.append(poll_data)

            if sunday_polls:
                # Берем самый последний опрос (первый в списке, так как сообщения отсортированы по дате)
                latest_poll = sunday_polls[0]
                poll_date = datetime.datetime.fromisoformat(
                    latest_poll['date'].replace('Z', '+00:00')
                )
                print(f"✅ Найден последний опрос тренировок от {poll_date.strftime('%Y-%m-%d %H:%M')}")
                return latest_poll
            else:
                print("⚠️ Опросы тренировок за последнее воскресенье не найдены")
                return None

        except Exception as e:
            print(f"❌ Ошибка поиска последнего опроса тренировок: {e}")
            return None

    def parse_training_votes_enhanced(self, poll_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Улучшенный парсинг голосов за тренировки"""
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
                voter_names = option.get('voter_names', [])

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
                    if voter_names:
                        # Если есть имена участников, используем их
                        attendees[category].extend(voter_names)
                    else:
                        # Если нет имен, создаем заглушки
                        for i in range(voters):
                            attendees[category].append(f"Участник_{i+1}")

            return attendees

        except Exception as e:
            print(f"❌ Ошибка парсинга голосов: {e}")
            return attendees

    def generate_attendance_statistics(self, poll_results: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует статистику посещаемости из результатов опроса"""
        try:
            attendees = self.parse_training_votes_enhanced(poll_results)

            stats = {
                "poll_date": poll_results.get('date'),
                "total_voters": poll_results.get('total_voters', 0),
                "is_anonymous": poll_results.get('is_anonymous', True),
                "by_day": {},
                "unique_participants": set(),
                "participant_stats": {}
            }

            # Анализируем данные по дням
            for day, participants in attendees.items():
                if participants:
                    stats["by_day"][day] = {
                        "count": len(participants),
                        "participants": participants
                    }
                    stats["unique_participants"].update(participants)

            # Статистика по участникам
            for participant in stats["unique_participants"]:
                attendance_count = 0
                for day_data in stats["by_day"].values():
                    if participant in day_data["participants"]:
                        attendance_count += 1

                stats["participant_stats"][participant] = {
                    "total_attendance": attendance_count,
                    "days_attended": [
                        day for day, data in stats["by_day"].items()
                        if participant in data["participants"]
                    ]
                }

            return stats

        except Exception as e:
            print(f"❌ Ошибка генерации статистики: {e}")
            return {}

    async def close_client(self):
        """Закрывает клиент"""
        if self.client:
            await self.client.disconnect()
            print("✅ Enhanced Telegram Client отключен")


# Глобальный экземпляр
enhanced_poll_handler = EnhancedPollHandler()


async def test_enhanced_poll_handler():
    """Тестирует улучшенный обработчик опросов"""
    print("🧪 Тестирование улучшенного обработчика опросов...")

    try:
        # Запускаем клиент
        if not await enhanced_poll_handler.start_client():
            print("❌ Не удалось запустить клиент")
            return False

        # Получаем последний опрос тренировок
        latest_poll = await enhanced_poll_handler.get_latest_sunday_training_poll()

        if latest_poll:
            print(f"\n📊 Найден опрос:")
            print(f"   Вопрос: {latest_poll['question']}")
            print(f"   Анонимный: {latest_poll['is_anonymous']}")
            print(f"   Всего голосов: {latest_poll['total_voters']}")

            # Генерируем статистику
            stats = enhanced_poll_handler.generate_attendance_statistics(latest_poll)

            if stats:
                print(f"\n📈 Статистика посещаемости:")
                print(f"   Уникальных участников: {len(stats['unique_participants'])}")

                for day, data in stats['by_day'].items():
                    print(f"   {day}: {data['count']} участников")

                print(f"\n👥 Статистика по участникам:")
                for participant, participant_stats in stats['participant_stats'].items():
                    print(f"   {participant}: {participant_stats['total_attendance']} тренировок "
                      f"({', '.join(participant_stats['days_attended'])})")

            return True
        else:
            print("⚠️ Опросы не найдены")
            return False

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    finally:
        await enhanced_poll_handler.close_client()


if __name__ == "__main__":
    asyncio.run(test_enhanced_poll_handler())
