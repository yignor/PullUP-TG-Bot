#!/usr/bin/env python3
"""
Упрощенный скрипт для создания голосований по расписанию игр PullUP
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

def create_poll_title(game):
    """Создает название голосования"""
    # Определяем тип команды
    if "Pull Up-Фарм" in game['pullup_team']:
        team_type = "развитие"
    else:
        team_type = "первый состав"
    
    # Формируем название
    title = f"Летняя лига, {team_type}, {game['opponent_team']}: {game['weekday']} ({game['date'][:8]}) {game['time']}, {game['venue']}"
    
    return title

async def create_schedule_polls_simple():
    """Создает голосования по расписанию (упрощенная версия)"""
    print("🏀 СОЗДАНИЕ ГОЛОСОВАНИЙ ПО РАСПИСАНИЮ (УПРОЩЕННАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    try:
        # Получаем настройки
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        topic_id = "1282"  # Топик для голосований
        
        if not bot_token:
            print("❌ BOT_TOKEN не настроен")
            return
        
        if not chat_id:
            print("❌ CHAT_ID не настроен")
            return
        
        print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
        print(f"✅ CHAT_ID: {chat_id}")
        print(f"✅ TOPIC_ID: {topic_id}")
        print()
        
        # Фиксированные данные игр из расписания
        pullup_games = [
            {
                'date': '20.08.2025',
                'time': '20.30',
                'weekday': 'Среда',
                'venue': 'ВО СШОР Малый 66',
                'pullup_team': 'Pull Up',
                'opponent_team': 'Кирпичный Завод'
            },
            {
                'date': '21.08.2025',
                'time': '21.45',
                'weekday': 'Четверг',
                'venue': 'MarvelHall',
                'pullup_team': 'Pull Up',
                'opponent_team': 'Lion'
            },
            {
                'date': '23.08.2025',
                'time': '11.10',
                'weekday': 'Суббота',
                'venue': 'MarvelHall',
                'pullup_team': 'Pull Up',
                'opponent_team': 'Quasar'
            }
        ]
        
        print(f"📅 Создаем голосования для {len(pullup_games)} игр PullUP")
        
        # Создаем бота
        bot = Bot(token=bot_token)
        
        # Создаем голосования для каждой игры
        for i, game in enumerate(pullup_games, 1):
            print(f"\n🏀 Игра {i}: {game['pullup_team']} vs {game['opponent_team']}")
            print(f"   Дата: {game['date']} ({game['weekday']})")
            print(f"   Время: {game['time']}")
            print(f"   Зал: {game['venue']}")
            
            # Создаем название голосования
            poll_title = create_poll_title(game)
            print(f"   Название голосования: {poll_title}")
            
            # Варианты ответов
            poll_options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            try:
                # Создаем голосование
                poll = await bot.send_poll(
                    chat_id=chat_id,
                    question=poll_title,
                    options=poll_options,
                    allows_multiple_answers=False,  # Единственный выбор
                    is_anonymous=False,  # Открытое голосование
                    message_thread_id=int(topic_id)
                )
                
                print(f"   ✅ Голосование создано! ID: {poll.message_id}")
                
            except Exception as e:
                print(f"   ❌ Ошибка создания голосования: {e}")
        
        print(f"\n🎯 СОЗДАНО ГОЛОСОВАНИЙ: {len(pullup_games)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_schedule_polls_simple())
