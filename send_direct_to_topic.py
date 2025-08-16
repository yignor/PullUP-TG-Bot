#!/usr/bin/env python3
"""
Скрипт для отправки сообщения прямо в топик "АНОНСЫ ТРЕНИРОВОК"
"""

import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def send_to_topic():
    """Отправляет сообщение в топик"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    bot = Bot(token=bot_token)
    
    # Попробуем несколько возможных ID топиков
    # Обычно ID топиков начинаются с 1, 2, 3 и т.д.
    possible_topic_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    print("🔍 Попытка отправки в топик 'АНОНСЫ ТРЕНИРОВОК'...")
    print("📋 Буду пробовать ID топиков:", possible_topic_ids)
    
    for topic_id in possible_topic_ids:
        try:
            print(f"\n📤 Пробую топик ID: {topic_id}")
            
            message = await bot.send_message(
                chat_id=chat_id,
                text=f"🏀 Тестовое сообщение в топик (ID: {topic_id})",
                message_thread_id=topic_id
            )
            
            print(f"✅ Успешно отправлено в топик ID: {topic_id}")
            print(f"📋 ID сообщения: {message.message_id}")
            print(f"\n🎯 НАЙДЕН ПРАВИЛЬНЫЙ ID ТОПИКА: {topic_id}")
            print(f"📝 Добавьте в .env файл:")
            print(f"ANNOUNCEMENTS_TOPIC_ID={topic_id}")
            
            return topic_id
            
        except Exception as e:
            print(f"❌ Топик ID {topic_id}: {str(e)[:50]}...")
            continue
    
    print("\n❌ Не удалось найти правильный ID топика")
    print("📝 Попробуйте ручной способ:")
    print("1. Откройте чат с топиками")
    print("2. Найдите топик 'АНОНСЫ ТРЕНИРОВОК'")
    print("3. Скопируйте ID топика из URL или интерфейса")
    print("4. Добавьте в .env: ANNOUNCEMENTS_TOPIC_ID=<ID>")

if __name__ == "__main__":
    asyncio.run(send_to_topic())
