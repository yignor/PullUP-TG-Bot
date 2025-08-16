#!/usr/bin/env python3
"""
Скрипт для загрузки переменных из .env файла и тестирования уведомлений
"""

import os
import asyncio
from dotenv import load_dotenv
from pullup_notifications import PullUPNotificationManager

def load_env_variables():
    """Загружает переменные из .env файла"""
    # Пробуем загрузить через python-dotenv
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        # Если python-dotenv не установлен, читаем файл вручную
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
    
    # Проверяем наличие необходимых переменных
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден в .env файле")
        return False
    
    if not chat_id:
        print("❌ CHAT_ID не найден в .env файле")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True

async def test_all_notifications():
    """Тестирует все типы уведомлений"""
    print("\n=== ТЕСТИРОВАНИЕ УВЕДОМЛЕНИЙ ===\n")
    
    # Загружаем переменные
    if not load_env_variables():
        return
    
    manager = PullUPNotificationManager()
    
    # Тест 1: Утреннее уведомление
    print("1. Тест утреннего уведомления:")
    try:
        # Получаем свежие данные
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        
        current_date = manager.extract_current_date(page_text)
        if current_date:
            pullup_games = manager.find_pullup_games(page_text, current_date)
            if pullup_games:
                await manager.send_morning_notification(pullup_games, html_content)
                print("✅ Утреннее уведомление отправлено")
            else:
                print("⚠️ Игры PullUP не найдены")
        else:
            print("❌ Не удалось извлечь дату")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    
    # Тест 2: Уведомление о завершении игры (победа)
    print("2. Тест уведомления о завершении игры (победа):")
    try:
        test_game = {
            'pullup_team': 'Pull Up',
            'opponent_team': 'IT Basket',
            'pullup_score': 85,
            'opponent_score': 72,
            'date': '16.08.2025'
        }
        await manager.send_finish_notification(test_game)
        print("✅ Уведомление о победе отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    
    # Тест 3: Уведомление о завершении игры (проигрыш)
    print("3. Тест уведомления о завершении игры (проигрыш):")
    try:
        test_game = {
            'pullup_team': 'Pull Up',
            'opponent_team': 'Маиле Карго',
            'pullup_score': 65,
            'opponent_score': 78,
            'date': '16.08.2025'
        }
        await manager.send_finish_notification(test_game)
        print("✅ Уведомление о проигрыше отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    
    # Тест 4: Уведомление о завершении игры (ничья)
    print("4. Тест уведомления о завершении игры (ничья):")
    try:
        test_game = {
            'pullup_team': 'Pull Up',
            'opponent_team': 'Тосно',
            'pullup_score': 75,
            'opponent_score': 75,
            'date': '16.08.2025'
        }
        await manager.send_finish_notification(test_game)
        print("✅ Уведомление о ничьей отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    asyncio.run(test_all_notifications())
