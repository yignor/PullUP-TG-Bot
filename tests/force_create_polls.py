#!/usr/bin/env python3
"""
Скрипт для принудительного создания голосований (для демонстрации)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def force_create_polls():
    """Принудительно создает голосования для демонстрации"""
    print("🏀 ПРИНУДИТЕЛЬНОЕ СОЗДАНИЕ ГОЛОСОВАНИЙ (ДЕМОНСТРАЦИЯ)")
    print("=" * 60)
    
    try:
        # Импортируем менеджер
        from schedule_polls import SchedulePollsManager
        
        # Создаем экземпляр менеджера
        manager = SchedulePollsManager()
        
        print(f"✅ Бот настроен: {manager.bot is not None}")
        print(f"✅ CHAT_ID: {manager.chat_id}")
        print(f"✅ TOPIC_ID: {manager.topic_id}")
        print()
        
        # Получаем расписание
        print("📡 Получаем расписание с сайта...")
        html_content = await manager.get_fresh_page_content()
        
        # Парсим расписание
        pullup_games = manager.parse_schedule(html_content)
        
        print(f"📅 Найдено игр PullUP в расписании: {len(pullup_games)}")
        
        if not pullup_games:
            print("❌ Игры PullUP в расписании не найдены")
            return
        
        # Создаем голосования для каждой игры
        created_count = 0
        for i, game in enumerate(pullup_games, 1):
            print(f"\n🏀 Игра {i}: {game['pullup_team']} vs {game['opponent_team']}")
            print(f"   Дата: {game['date']} ({game['weekday']})")
            print(f"   Время: {game['time']}")
            print(f"   Зал: {game['venue']}")
            
            # Проверяем, создано ли уже голосование
            if manager.is_poll_created(game):
                print(f"   ✅ Голосование уже создано ранее")
                continue
            
            # Создаем название голосования
            poll_title = manager.create_poll_title(game)
            print(f"   Название голосования: {poll_title}")
            
            # Варианты ответов
            poll_options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            
            try:
                # Создаем голосование
                poll = await manager.bot.send_poll(
                    chat_id=manager.chat_id,
                    question=poll_title,
                    options=poll_options,
                    allows_multiple_answers=False,  # Единственный выбор
                    is_anonymous=False,  # Открытое голосование
                    message_thread_id=int(manager.topic_id)
                )
                
                # Отмечаем голосование как созданное
                manager.mark_poll_created(game, poll.message_id)
                
                print(f"   ✅ Голосование создано! ID: {poll.message_id}")
                created_count += 1
                
            except Exception as e:
                print(f"   ❌ Ошибка создания голосования: {e}")
        
        print(f"\n🎯 СОЗДАНО НОВЫХ ГОЛОСОВАНИЙ: {created_count}")
        print(f"📊 Всего созданных голосований: {len(manager.created_polls)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_create_polls())
