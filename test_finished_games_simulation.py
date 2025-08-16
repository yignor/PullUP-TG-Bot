#!/usr/bin/env python3
"""
Скрипт для тестирования логики завершенных игр с симуляцией
"""

import asyncio
import os
from dotenv import load_dotenv
from pullup_notifications import PullUPNotificationManager

def load_env_variables():
    """Загружает переменные из .env файла"""
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Переменные загружены из .env файла")
        except FileNotFoundError:
            print("❌ Файл .env не найден")
            return False
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True

async def test_finished_games_simulation():
    """Тестирует логику завершенных игр с симуляцией"""
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕННЫХ ИГР (СИМУЛЯЦИЯ) ===\n")
    
    if not load_env_variables():
        return
    
    manager = PullUPNotificationManager()
    
    # Симулируем завершенные игры
    print("1. Симуляция завершенных игр...")
    
    # Тест 1: Победа Pull Up
    print("\n2. Тест уведомления о победе Pull Up:")
    test_game_1 = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'IT Basket',
        'pullup_score': 85,
        'opponent_score': 72,
        'date': '16.08.2025',
        'game_link': 'http://letobasket.ru/game.html?gameId=921733&apiUrl=https://reg.infobasket.su&lang=ru'
    }
    
    try:
        await manager.send_finish_notification(test_game_1)
        print("✅ Уведомление о победе отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: Проигрыш Pull Up
    print("\n3. Тест уведомления о проигрыше Pull Up:")
    test_game_2 = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'Маиле Карго',
        'pullup_score': 65,
        'opponent_score': 78,
        'date': '16.08.2025',
        'game_link': 'http://letobasket.ru/game.html?gameId=921726&apiUrl=https://reg.infobasket.su&lang=ru'
    }
    
    try:
        await manager.send_finish_notification(test_game_2)
        print("✅ Уведомление о проигрыше отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Ничья
    print("\n4. Тест уведомления о ничьей:")
    test_game_3 = {
        'pullup_team': 'Pull Up',
        'opponent_team': 'Тосно',
        'pullup_score': 75,
        'opponent_score': 75,
        'date': '16.08.2025',
        'game_link': 'http://letobasket.ru/game.html?gameId=921727&apiUrl=https://reg.infobasket.su&lang=ru'
    }
    
    try:
        await manager.send_finish_notification(test_game_3)
        print("✅ Уведомление о ничьей отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
    print("\n📋 Проверьте Telegram чат для подтверждения отправки уведомлений")

if __name__ == "__main__":
    asyncio.run(test_finished_games_simulation())
