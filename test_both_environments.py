#!/usr/bin/env python3
"""
Скрипт для тестирования обоих окружений одновременно
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

def load_all_env_variables():
    """Загружает все переменные из .env файла"""
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
            return False, None, None, None, None
    
    # Основные настройки (текущие)
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    # Тестовые настройки
    test_bot_token = os.getenv('TEST_BOT_TOKEN')
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False, None, None, None, None
    
    if not test_bot_token or not test_chat_id:
        print("❌ TEST_BOT_TOKEN или TEST_CHAT_ID не найдены")
        return False, None, None, None, None
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    print(f"✅ TEST_BOT_TOKEN: {test_bot_token[:10]}...")
    print(f"✅ TEST_CHAT_ID: {test_chat_id}")
    
    return True, bot_token, chat_id, test_bot_token, test_chat_id

async def test_both_environments():
    """Тестирует оба окружения одновременно"""
    print("\n=== ТЕСТИРОВАНИЕ ОБОИХ ОКРУЖЕНИЙ ===\n")
    
    success, bot_token, chat_id, test_bot_token, test_chat_id = load_all_env_variables()
    if not success:
        return
    
    try:
        # Создаем два бота
        main_bot = Bot(token=bot_token)
        test_bot = Bot(token=test_bot_token)
        print("✅ Оба бота инициализированы")
        
        # Определяем режимы
        main_mode = "🧪 ТЕСТОВЫЙ" if chat_id == "-15573582" else "🏭 ПРОДАКШН"
        test_mode = "🧪 ТЕСТОВЫЙ" if test_chat_id == "-15573582" else "🏭 ПРОДАКШН"
        
        print(f"📋 Основной чат: {main_mode} (CHAT_ID: {chat_id})")
        print(f"📋 Тестовый чат: {test_mode} (CHAT_ID: {test_chat_id})")
        
        # Тестовое сообщение в основной чат
        print(f"\n1. Отправка в основной чат ({main_mode})...")
        main_message = f"📱 ОСНОВНОЙ ЧАТ ({main_mode})\n\nЭто сообщение отправлено в основной чат.\nВремя: {asyncio.get_event_loop().time()}"
        
        await main_bot.send_message(chat_id=chat_id, text=main_message)
        print(f"✅ Сообщение отправлено в основной чат ({main_mode})!")
        
        # Тестовое сообщение в тестовый чат
        print(f"\n2. Отправка в тестовый чат ({test_mode})...")
        test_message = f"🧪 ТЕСТОВЫЙ ЧАТ ({test_mode})\n\nЭто сообщение отправлено в тестовый чат.\nВремя: {asyncio.get_event_loop().time()}"
        
        await test_bot.send_message(chat_id=test_chat_id, text=test_message)
        print(f"✅ Сообщение отправлено в тестовый чат ({test_mode})!")
        
        # Тестовые опросы
        print(f"\n3. Создание опросов в оба чата...")
        
        # Опрос в основной чат
        main_question = f"📱 Основной чат ({main_mode})"
        main_options = [
            "✅ Работает",
            "❌ Не работает",
            "⚠️ Требует проверки"
        ]
        
        main_poll = await main_bot.send_poll(
            chat_id=chat_id,
            question=main_question,
            options=main_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation=f"Тестовый опрос в основном чате ({main_mode})"
        )
        print(f"✅ Опрос создан в основном чате ({main_mode})!")
        
        # Опрос в тестовый чат
        test_question = f"🧪 Тестовый чат ({test_mode})"
        test_options = [
            "✅ Работает",
            "❌ Не работает", 
            "⚠️ Требует проверки"
        ]
        
        test_poll = await test_bot.send_poll(
            chat_id=test_chat_id,
            question=test_question,
            options=test_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation=f"Тестовый опрос в тестовом чате ({test_mode})"
        )
        print(f"✅ Опрос создан в тестовом чате ({test_mode})!")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте оба Telegram чата для подтверждения")
        print(f"📱 Основной чат: {main_mode}")
        print(f"🧪 Тестовый чат: {test_mode}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_both_environments())
