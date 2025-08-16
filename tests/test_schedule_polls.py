#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы голосований по расписанию
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def test_schedule_polls():
    """Тестирует систему голосований по расписанию"""
    print("🧪 ТЕСТ СИСТЕМЫ ГОЛОСОВАНИЙ ПО РАСПИСАНИЮ")
    print("=" * 60)
    
    try:
        # Импортируем менеджер
        from schedule_polls import SchedulePollsManager
        
        # Создаем экземпляр менеджера
        manager = SchedulePollsManager()
        
        print(f"✅ Бот настроен: {manager.bot is not None}")
        print(f"✅ CHAT_ID: {manager.chat_id}")
        print(f"✅ TOPIC_ID: {manager.topic_id}")
        print(f"✅ Загружено созданных голосований: {len(manager.created_polls)}")
        print()
        
        # Получаем расписание
        print("📡 Получаем расписание с сайта...")
        html_content = await manager.get_fresh_page_content()
        
        # Парсим расписание
        pullup_games = manager.parse_schedule(html_content)
        
        print(f"📅 Найдено игр PullUP в расписании: {len(pullup_games)}")
        
        if pullup_games:
            print("\n🏀 ИГРЫ PULLUP В РАСПИСАНИИ:")
            for i, game in enumerate(pullup_games, 1):
                print(f"   {i}. {game['pullup_team']} vs {game['opponent_team']}")
                print(f"      Дата: {game['date']} ({game['weekday']})")
                print(f"      Время: {game['time']}")
                print(f"      Зал: {game['venue']}")
                
                # Проверяем, создано ли уже голосование
                poll_id = manager.get_poll_id(game)
                is_created = manager.is_poll_created(game)
                print(f"      ID голосования: {poll_id}")
                print(f"      Создано: {'✅ Да' if is_created else '❌ Нет'}")
                
                if not is_created:
                    # Показываем, как будет выглядеть название голосования
                    poll_title = manager.create_poll_title(game)
                    print(f"      Название голосования: {poll_title}")
                
                print()
        
        # Тестируем создание голосования (только для демонстрации)
        print("🧪 ТЕСТИРОВАНИЕ СОЗДАНИЯ ГОЛОСОВАНИЯ:")
        print("(В реальной работе голосования создаются только в 10:00-10:05)")
        
        if pullup_games:
            test_game = pullup_games[0]
            print(f"   Тестовая игра: {test_game['pullup_team']} vs {test_game['opponent_team']}")
            
            poll_title = manager.create_poll_title(test_game)
            print(f"   Название голосования: {poll_title}")
            
            poll_options = [
                "✅ Готов",
                "❌ Нет", 
                "👨‍🏫 Тренер"
            ]
            print(f"   Варианты ответов: {poll_options}")
            
            # Проверяем, создано ли уже голосование
            if manager.is_poll_created(test_game):
                print("   ✅ Голосование уже создано ранее")
            else:
                print("   ❌ Голосование еще не создано")
        
        print("\n🎯 ТЕСТ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schedule_polls())
