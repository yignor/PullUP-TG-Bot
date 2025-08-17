#!/usr/bin/env python3
"""
Модуль для сбора результатов голосований по расписанию игр PullUP
"""

import os
import asyncio
import datetime
import json
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
SCHEDULE_TOPIC_ID = "1282"  # Топик для голосований по расписанию

class SchedulePollResultsHandler:
    """Обработчик результатов голосований по расписанию"""
    
    def __init__(self):
        self.client = None
        self._init_telegram_client()
    
    def _init_telegram_client(self):
        """Инициализация Telegram Client API"""
        try:
            if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE]):
                print("⚠️ Переменные для Telegram Client API не настроены")
                print("   Нужно: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
                self.client = None
                return
            
            # Импортируем только при необходимости
            from telethon import TelegramClient
            
            self.client = TelegramClient(
                'schedule_poll_session',
                int(TELEGRAM_API_ID),
                TELEGRAM_API_HASH
            )
            print("✅ Telegram Client API инициализирован для голосований по расписанию")
            
        except ImportError:
            print("⚠️ telethon не установлен. Установите: pip install telethon")
            self.client = None
        except Exception as e:
            print(f"❌ Ошибка инициализации Telegram Client: {e}")
            self.client = None
    
    async def start_client(self):
        """Запускает клиент"""
        if not self.client:
            print("⚠️ Telegram Client не инициализирован (переменные окружения не настроены)")
            return False
        
        try:
            await self.client.start(phone=TELEGRAM_PHONE)
            print("✅ Telegram Client подключен")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения клиента: {e}")
            return False
    
    async def get_poll_results(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Получает результаты голосования по ID сообщения"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return None
        
        try:
            # Получаем сообщение с голосованием
            message = await self.client.get_messages(
                int(CHAT_ID),
                ids=message_id
            )
            
            if not message or not message.poll:
                print(f"❌ Сообщение {message_id} не содержит голосование")
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
                'date': message.date.isoformat(),
                'topic_id': getattr(message, 'reply_to', None)
            }
            
            # Обрабатываем варианты ответов
            for option in poll.answers:
                option_data = {
                    'text': option.text,
                    'voters': option.voters,
                    'option_id': option.option
                }
                results['options'].append(option_data)
            
            print(f"✅ Получены результаты голосования: {poll.question}")
            return results
            
        except Exception as e:
            print(f"❌ Ошибка получения результатов голосования: {e}")
            return None
    
    async def get_schedule_polls(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Получает все голосования по расписанию за последние N дней"""
        if not self.client:
            print("❌ Telegram Client не инициализирован")
            return []
        
        try:
            # Ищем голосования в топике 1282
            since = datetime.datetime.now() - datetime.timedelta(days=days_back)
            
            # Получаем сообщения из топика
            messages = await self.client.get_messages(
                int(CHAT_ID),
                search='Летняя лига',
                limit=100,
                offset_date=since
            )
            
            schedule_polls = []
            for message in messages:
                if message.poll and "Летняя лига" in message.poll.question:
                    poll_data = await self.get_poll_results(message.id)
                    if poll_data:
                        schedule_polls.append(poll_data)
            
            print(f"✅ Найдено {len(schedule_polls)} голосований по расписанию")
            return schedule_polls
            
        except Exception as e:
            print(f"❌ Ошибка поиска голосований по расписанию: {e}")
            return []
    
    def parse_schedule_votes(self, poll_results: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит голоса из результатов голосования по расписанию"""
        try:
            # Извлекаем информацию об игре из вопроса
            question = poll_results.get('question', '')
            
            # Парсим информацию об игре
            game_info = self.parse_game_info_from_question(question)
            
            # Собираем результаты голосования
            votes = {
                'ready': 0,
                'not_ready': 0,
                'coach': 0,
                'total': poll_results.get('total_voters', 0)
            }
            
            # Обрабатываем каждый вариант ответа
            for option in poll_results.get('options', []):
                option_text = option.get('text', '').lower()
                voters = option.get('voters', 0)
                
                if 'готов' in option_text:
                    votes['ready'] = voters
                elif 'нет' in option_text:
                    votes['not_ready'] = voters
                elif 'тренер' in option_text:
                    votes['coach'] = voters
            
            return {
                'game_info': game_info,
                'votes': votes,
                'poll_date': poll_results.get('date'),
                'message_id': poll_results.get('message_id')
            }
            
        except Exception as e:
            print(f"❌ Ошибка парсинга голосов: {e}")
            return {}
    
    def parse_game_info_from_question(self, question: str) -> Dict[str, str]:
        """Извлекает информацию об игре из вопроса голосования"""
        try:
            # Пример: "Летняя лига, первый состав, Кирпичный Завод: Среда (20.08.20) 20.30, ВО СШОР Малый 66"
            
            game_info = {
                'league': 'Летняя лига',
                'team_type': '',
                'opponent': '',
                'weekday': '',
                'date': '',
                'time': '',
                'venue': ''
            }
            
            # Разбираем вопрос по частям
            parts = question.split(', ')
            if len(parts) >= 3:
                game_info['league'] = parts[0]
                game_info['team_type'] = parts[1]
                
                # Обрабатываем третью часть с соперником и деталями
                opponent_part = parts[2]
                if ':' in opponent_part:
                    opponent, details = opponent_part.split(':', 1)
                    game_info['opponent'] = opponent.strip()
                    
                    # Парсим детали
                    details = details.strip()
                    
                    # Ищем день недели и дату
                    import re
                    weekday_match = re.search(r'(\w+)\s*\((\d{2}\.\d{2}\.\d{2})\)', details)
                    if weekday_match:
                        game_info['weekday'] = weekday_match.group(1)
                        game_info['date'] = weekday_match.group(2)
                    
                    # Ищем время
                    time_match = re.search(r'(\d{2}:\d{2})', details)
                    if time_match:
                        game_info['time'] = time_match.group(1)
                    
                    # Ищем зал (после запятой)
                    if ',' in details:
                        venue_part = details.split(',', 1)[1]
                        game_info['venue'] = venue_part.strip()
            
            return game_info
            
        except Exception as e:
            print(f"❌ Ошибка парсинга информации об игре: {e}")
            return {}
    
    async def get_game_attendance_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Получает сводку посещаемости игр за последние N дней"""
        try:
            schedule_polls = await self.get_schedule_polls(days_back)
            
            summary = {
                'total_games': len(schedule_polls),
                'games': [],
                'total_ready': 0,
                'total_not_ready': 0,
                'total_coach': 0
            }
            
            for poll in schedule_polls:
                parsed_data = self.parse_schedule_votes(poll)
                if parsed_data:
                    game_info = parsed_data.get('game_info', {})
                    votes = parsed_data.get('votes', {})
                    
                    game_summary = {
                        'opponent': game_info.get('opponent', 'Неизвестно'),
                        'date': game_info.get('date', ''),
                        'time': game_info.get('time', ''),
                        'venue': game_info.get('venue', ''),
                        'team_type': game_info.get('team_type', ''),
                        'ready': votes.get('ready', 0),
                        'not_ready': votes.get('not_ready', 0),
                        'coach': votes.get('coach', 0),
                        'total': votes.get('total', 0)
                    }
                    
                    summary['games'].append(game_summary)
                    summary['total_ready'] += votes.get('ready', 0)
                    summary['total_not_ready'] += votes.get('not_ready', 0)
                    summary['total_coach'] += votes.get('coach', 0)
            
            return summary
            
        except Exception as e:
            print(f"❌ Ошибка получения сводки посещаемости: {e}")
            return {}
    
    async def close_client(self):
        """Закрывает клиент"""
        if self.client:
            await self.client.disconnect()
            print("✅ Telegram Client отключен")

# Глобальный экземпляр
schedule_poll_handler = SchedulePollResultsHandler()

async def test_schedule_poll_results():
    """Тестирует получение результатов голосований по расписанию"""
    print("🧪 Тестирование получения результатов голосований по расписанию...")
    
    try:
        # Запускаем клиент
        if not await schedule_poll_handler.start_client():
            print("❌ Не удалось запустить клиент")
            return False
        
        # Получаем голосования по расписанию
        schedule_polls = await schedule_poll_handler.get_schedule_polls(days_back=7)
        
        if schedule_polls:
            print(f"\n📊 Найдено {len(schedule_polls)} голосований по расписанию:")
            for i, poll in enumerate(schedule_polls, 1):
                print(f"\n{i}. {poll['question']}")
                print(f"   Всего голосов: {poll['total_voters']}")
                for option in poll['options']:
                    print(f"   - {option['text']}: {option['voters']} голосов")
                
                # Парсим результаты
                parsed_data = schedule_poll_handler.parse_schedule_votes(poll)
                if parsed_data:
                    game_info = parsed_data.get('game_info', {})
                    votes = parsed_data.get('votes', {})
                    
                    print(f"   📅 Игра: {game_info.get('opponent', 'Неизвестно')}")
                    print(f"   📊 Готовы: {votes.get('ready', 0)}, Не готовы: {votes.get('not_ready', 0)}, Тренер: {votes.get('coach', 0)}")
        else:
            print("📊 Голосования по расписанию не найдены")
        
        # Получаем сводку посещаемости
        summary = await schedule_poll_handler.get_game_attendance_summary(days_back=7)
        if summary:
            print(f"\n📈 СВОДКА ПОСЕЩАЕМОСТИ:")
            print(f"   Всего игр: {summary['total_games']}")
            print(f"   Всего готовы: {summary['total_ready']}")
            print(f"   Всего не готовы: {summary['total_not_ready']}")
            print(f"   Всего тренер: {summary['total_coach']}")
            
            if summary['games']:
                print(f"\n🏀 ДЕТАЛИ ПО ИГРАМ:")
                for game in summary['games']:
                    print(f"   {game['opponent']} ({game['date']} {game['time']}): Готовы {game['ready']}, Не готовы {game['not_ready']}, Тренер {game['coach']}")
        
        await schedule_poll_handler.close_client()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_schedule_poll_results())
