#!/usr/bin/env python3
"""
Скрипт для тестирования с правильными настройками продакшн и тест чатов
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

async def test_both_with_correct_settings():
    """Тестирует оба окружения с правильными настройками"""
    print("\n=== ТЕСТИРОВАНИЕ С ПРАВИЛЬНЫМИ НАСТРОЙКАМИ ===\n")
    
    # Загружаем переменные
    try:
        load_dotenv()
        print("✅ Переменные загружены")
    except Exception as e:
        print(f"❌ Ошибка загрузки переменных: {e}")
        return
    
    # Настройки для тестирования
    bot_token = "7772125141:AAHqFYGm3I6MW516aCq3K0FFjK2EGKk0wtw"
    
    # Продакшн чат
    prod_chat_id = "-1001535261616"
    
    # Тестовый чат  
    test_chat_id = "-15573582"
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"🏭 ПРОДАКШН CHAT_ID: {prod_chat_id}")
    print(f"🧪 ТЕСТОВЫЙ CHAT_ID: {test_chat_id}")
    
    try:
        # Создаем бота
        bot = Bot(token=bot_token)
        print("✅ Бот инициализирован")
        
        # Тестовое сообщение в продакшн чат
        print(f"\n1. Отправка в ПРОДАКШН чат...")
        prod_message = "🏭 ПРОДАКШН ЧАТ\n\nЭто сообщение отправлено в продакшн чат.\nВремя: " + str(asyncio.get_event_loop().time())
        
        await bot.send_message(chat_id=prod_chat_id, text=prod_message)
        print("✅ Сообщение отправлено в ПРОДАКШН чат!")
        
        # Тестовое сообщение в тестовый чат
        print(f"\n2. Отправка в ТЕСТОВЫЙ чат...")
        test_message = "🧪 ТЕСТОВЫЙ ЧАТ\n\nЭто сообщение отправлено в тестовый чат.\nВремя: " + str(asyncio.get_event_loop().time())
        
        await bot.send_message(chat_id=test_chat_id, text=test_message)
        print("✅ Сообщение отправлено в ТЕСТОВЫЙ чат!")
        
        # Тестовые опросы
        print(f"\n3. Создание опросов в оба чата...")
        
        # Опрос в продакшн чат
        prod_question = "🏭 Продакшн чат"
        prod_options = [
            "✅ Работает",
            "❌ Не работает",
            "⚠️ Требует проверки"
        ]
        
        prod_poll = await bot.send_poll(
            chat_id=prod_chat_id,
            question=prod_question,
            options=prod_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation="Тестовый опрос в продакшн чате"
        )
        print("✅ Опрос создан в ПРОДАКШН чате!")
        
        # Опрос в тестовый чат
        test_question = "🧪 Тестовый чат"
        test_options = [
            "✅ Работает",
            "❌ Не работает", 
            "⚠️ Требует проверки"
        ]
        
        test_poll = await bot.send_poll(
            chat_id=test_chat_id,
            question=test_question,
            options=test_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation="Тестовый опрос в тестовом чате"
        )
        print("✅ Опрос создан в ТЕСТОВОМ чате!")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте оба Telegram чата для подтверждения")
        print("🏭 ПРОДАКШН чат: -1001535261616")
        print("🧪 ТЕСТОВЫЙ чат: -15573582")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_both_with_correct_settings())
