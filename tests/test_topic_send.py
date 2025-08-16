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
    chat_id = os.getenv('CHAT_ID')
    topic_id = os.getenv('ANNOUNCEMENTS_TOPIC_ID')
    
    print("🧪 ТЕСТ ОТПРАВКИ В ТОПИК")
    print("=" * 30)
    
    # Проверяем настройки
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not chat_id:
        print("❌ CHAT_ID не настроен")
        return
    
    if not topic_id:
        print("❌ ANNOUNCEMENTS_TOPIC_ID не настроен")
        print("📝 Сначала настройте ID топика: python manual_topic_id.py")
        return
    
    print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
    print(f"✅ CHAT_ID: {chat_id}")
    print(f"✅ ANNOUNCEMENTS_TOPIC_ID: {topic_id}")
    
    bot = Bot(token=bot_token)
    
    try:
        print("\n📤 Отправляю тестовое сообщение в топик...")
        
        # Отправляем тестовое сообщение
        message = await bot.send_message(
            chat_id=chat_id,
            text="🧪 Тестовое сообщение в топик 'АНОНСЫ ТРЕНИРОВОК'",
            message_thread_id=int(topic_id)
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
