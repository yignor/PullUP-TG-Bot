#!/usr/bin/env python3
"""
Скрипт для получения ID топика "АНОНСЫ ТРЕНИРОВОК"
"""

import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def get_topic_id():
    """Получает ID топика через отправку тестового сообщения"""
    
    # Получаем настройки
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Ошибка: BOT_TOKEN или CHAT_ID не настроены")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        print("📤 Отправляю тестовое сообщение в топик 'АНОНСЫ ТРЕНИРОВОК'...")
        
        # Отправляем тестовое сообщение
        message = await bot.send_message(
            chat_id=chat_id,
            text="🔍 Тестовое сообщение для определения ID топика",
            message_thread_id=None  # Отправляем в общий чат
        )
        
        print(f"✅ Сообщение отправлено! ID сообщения: {message.message_id}")
        print(f"📋 Chat ID: {chat_id}")
        print("\n📝 Теперь:")
        print("1. Перейдите в чат и переместите это сообщение в топик 'АНОНСЫ ТРЕНИРОВОК'")
        print("2. Или отправьте новое сообщение от бота прямо в топик")
        print("3. Затем выполните следующий шаг...")
        
        # Показываем ссылку для получения обновлений
        print(f"\n🔗 Проверьте обновления по ссылке:")
        print(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        
        print("\n📋 В ответе найдите:")
        print("- 'message_thread_id' - это и есть ID топика")
        print("- Если топик не найден, попробуйте отправить сообщение от бота прямо в топик")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(get_topic_id())
