#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки в топик "АНОНСЫ ТРЕНИРОВОК"
"""

import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_topic_send():
    """Тестирует отправку сообщения в топик"""
    
    # Получаем настройки
    bot_token = os.getenv('BOT_TOKEN')
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    print("🧪 ТЕСТ ОТПРАВКИ В ТЕСТОВЫЙ КАНАЛ")
    print("=" * 40)
    
    # Проверяем настройки
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not test_chat_id:
        print("❌ TEST_CHAT_ID не настроен")
        print("📝 Добавьте TEST_CHAT_ID в .env для тестирования")
        return
    
    print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
    print(f"✅ TEST_CHAT_ID: {test_chat_id}")
    print("🧪 Отправка в ТЕСТОВЫЙ канал")
    
    bot = Bot(token=bot_token)
    
    try:
        print("\n📤 Отправляю тестовое сообщение в топик...")
        
        # Отправляем тестовое сообщение в ТЕСТОВЫЙ канал
        message = await bot.send_message(
            chat_id=test_chat_id,
            text="🧪 ТЕСТОВОЕ СООБЩЕНИЕ - Проверка отправки в тестовый канал"
        )
        
        print(f"✅ Сообщение успешно отправлено!")
        print(f"📋 ID сообщения: {message.message_id}")
        print(f"📋 Время отправки: {message.date}")
        
        print("\n🎯 Топик настроен правильно!")
        print("📝 Теперь можно настроить остальные компоненты системы")
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        print("\n🔍 Возможные причины:")
        print("1. Неправильный ID топика")
        print("2. Бот не имеет прав на отправку в топик")
        print("3. Топик не существует")
        print("\n📝 Проверьте настройки и попробуйте снова")

if __name__ == "__main__":
    asyncio.run(test_topic_send())
