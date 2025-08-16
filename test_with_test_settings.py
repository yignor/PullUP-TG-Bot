#!/usr/bin/env python3
"""
Скрипт для тестирования с тестовыми настройками
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

def load_test_env_variables():
    """Загружает тестовые переменные из .env файла"""
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
            return False, None, None
    
    # Используем тестовые настройки
    bot_token = os.getenv('TEST_BOT_TOKEN')
    chat_id = os.getenv('TEST_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ TEST_BOT_TOKEN или TEST_CHAT_ID не найдены")
        return False, None, None
    
    print(f"✅ TEST_BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ TEST_CHAT_ID: {chat_id}")
    print("🔧 Используются ТЕСТОВЫЕ настройки")
    return True, bot_token, chat_id

async def test_with_test_settings():
    """Тестирует функционал с тестовыми настройками"""
    print("\n=== ТЕСТИРОВАНИЕ С ТЕСТОВЫМИ НАСТРОЙКАМИ ===\n")
    
    success, bot_token, chat_id = load_test_env_variables()
    if not success:
        return
    
    try:
        bot = Bot(token=bot_token)
        print("✅ Бот инициализирован с тестовыми настройками")
        
        # Тестовое сообщение
        print(f"1. Отправка тестового сообщения...")
        test_message = "🧪 ТЕСТОВОЕ СООБЩЕНИЕ\n\nЭто сообщение отправлено с тестовыми настройками для проверки функционала."
        
        await bot.send_message(chat_id=chat_id, text=test_message)
        print("✅ Тестовое сообщение отправлено!")
        
        # Тестовый опрос
        print(f"\n2. Создание тестового опроса...")
        test_question = "🧪 Тестовый опрос"
        test_options = [
            "✅ Работает",
            "❌ Не работает",
            "⚠️ Требует доработки"
        ]
        
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=test_question,
            options=test_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation="Тестовый опрос для проверки функционала"
        )
        
        print("✅ Тестовый опрос создан!")
        print(f"   Вопрос: {poll.poll.question}")
        print(f"   Варианты: {poll.poll.options}")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте тестовый Telegram чат для подтверждения")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_test_settings())
