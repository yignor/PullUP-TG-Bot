#!/usr/bin/env python3
"""
Тест для игр на 16.08.2025 с правильными командами и ссылками
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def test_yesterday_games():
    """Тестирует игры на 16.08.2025"""
    print("🧪 ТЕСТ ИГР НА 16.08.2025")
    print("=" * 60)
    
    try:
        # Создаем тестовую версию менеджера для тестового канала
        from test_pullup_notifications import TestPullUPNotificationManager
        test_manager = TestPullUPNotificationManager()
        
        # Игры на 16.08.2025
        yesterday_games = [
            {
                'pullup_team': 'Pull Up',
                'opponent_team': 'Маиле Карго',
                'pullup_score': 56,
                'opponent_score': 78,
                'date': '16.08.2025',
                'game_link': 'P2025/podrobno.php?id=230&id1=S'
            },
            {
                'pullup_team': 'Pull Up-Фарм',
                'opponent_team': 'IT Basket',
                'pullup_score': 61,
                'opponent_score': 43,
                'date': '16.08.2025',
                'game_link': 'P2025/podrobno.php?id=230&id1=S'
            }
        ]
        
        print(f"📅 Отправляем уведомления о {len(yesterday_games)} играх на 16.08.2025")
        print()
        
        for i, game in enumerate(yesterday_games, 1):
            print(f"🏀 Игра {i}: {game['pullup_team']} vs {game['opponent_team']}")
            print(f"   Счет: {game['pullup_score']} : {game['opponent_score']}")
            print(f"   Ссылка: {game['game_link']}")
            print()
            
            # Отправляем уведомление в тестовый канал
            await test_manager.send_test_finish_notification(game)
            print(f"✅ Уведомление отправлено: {game['pullup_team']} vs {game['opponent_team']}")
            print()
        
        print("🎯 ВСЕ УВЕДОМЛЕНИЯ ОТПРАВЛЕНЫ В ТЕСТОВЫЙ КАНАЛ")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_yesterday_games())
