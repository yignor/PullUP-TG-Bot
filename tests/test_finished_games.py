#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленной функции check_finished_games
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def test_finished_games():
    """Тестирует исправленную функцию check_finished_games"""
    print("🧪 ТЕСТ ИСПРАВЛЕННОЙ ФУНКЦИИ CHECK_FINISHED_GAMES")
    print("=" * 60)
    
    try:
        # Импортируем PullUPNotificationManager
        from pullup_notifications import PullUPNotificationManager
        
        # Создаем экземпляр менеджера
        manager = PullUPNotificationManager()
        
        # Получаем свежий контент
        print("📡 Получаем данные с сайта...")
        html_content = await manager.get_fresh_page_content()
        
        # Извлекаем текущую дату
        current_date = manager.extract_current_date(html_content)
        if not current_date:
            print("❌ Не удалось извлечь текущую дату")
            return
        
        print(f"📅 Текущая дата: {current_date}")
        
        # Проверяем завершенные игры
        print("\n🔍 Проверяем завершенные игры...")
        finished_games = manager.check_finished_games(html_content, current_date)
        
        print(f"\n🎯 РЕЗУЛЬТАТ:")
        print(f"   Найдено завершенных игр: {len(finished_games)}")
        
        if finished_games:
            print("\n🏁 ЗАВЕРШЕННЫЕ ИГРЫ:")
            for i, game in enumerate(finished_games, 1):
                print(f"   {i}. {game['pullup_team']} vs {game['opponent_team']}")
                print(f"      Счет: {game['pullup_score']} : {game['opponent_score']}")
                print(f"      Дата: {game['date']}")
                if game.get('game_link'):
                    print(f"      Ссылка: {game['game_link']}")
                print()
        else:
            print("❌ Завершенных игр не найдено")
        
        # Тестируем отправку уведомлений в тестовый канал
        if finished_games:
            print("📤 Тестируем отправку уведомлений в тестовый канал...")
            
            # Создаем тестовую версию менеджера для тестового канала
            from test_pullup_notifications import TestPullUPNotificationManager
            test_manager = TestPullUPNotificationManager()
            
            for game in finished_games:
                await test_manager.send_test_finish_notification(game)
                print(f"✅ Уведомление отправлено: {game['pullup_team']} vs {game['opponent_team']}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_finished_games())
