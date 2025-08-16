#!/usr/bin/env python3
"""
Скрипт для тестирования продакшн настроек
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

def load_production_env_variables():
    """Загружает продакшн переменные из .env файла"""
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
    
    # Используем продакшн настройки
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False, None, None
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    
    if chat_id == "-1001535261616":
        print("🏭 Используются ПРОДАКШН настройки")
    elif chat_id == "-15573582":
        print("🧪 Используются ТЕСТОВЫЕ настройки")
    else:
        print(f"⚠️ Неизвестный CHAT_ID: {chat_id}")
    
    return True, bot_token, chat_id

async def test_production_settings():
    """Тестирует продакшн настройки"""
    print("\n=== ТЕСТИРОВАНИЕ ПРОДАКШН НАСТРОЕК ===\n")
    
    success, bot_token, chat_id = load_production_env_variables()
    if not success:
        return
    
    try:
        bot = Bot(token=bot_token)
        print("✅ Бот инициализирован")
        
        # Тестовое сообщение в продакшн
        print(f"1. Отправка тестового сообщения в продакшн...")
        test_message = "🏭 ПРОДАКШН ТЕСТ\n\nЭто сообщение отправлено в продакшн чат для проверки настроек."
        
        await bot.send_message(chat_id=chat_id, text=test_message)
        print("✅ Тестовое сообщение отправлено в продакшн!")
        
        # Тестовый опрос в продакшн
        print(f"\n2. Создание тестового опроса в продакшн...")
        test_question = "🏭 Продакшн тест"
        test_options = [
            "✅ Настройки работают",
            "❌ Настройки не работают",
            "⚠️ Требует проверки"
        ]
        
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=test_question,
            options=test_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation="Тестовый опрос для проверки продакшн настроек"
        )
        
        print("✅ Тестовый опрос создан в продакшн!")
        print(f"   Вопрос: {poll.poll.question}")
        print(f"   Варианты: {poll.poll.options}")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте продакшн Telegram чат для подтверждения")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_production_settings())
