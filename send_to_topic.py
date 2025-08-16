#!/usr/bin/env python3
"""
Скрипт для отправки сообщения в топик "АНОНСЫ ТРЕНИРОВОК"
"""

import os
import asyncio
import aiohttp
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def get_forum_topics():
    """Получает список топиков в чате"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Ошибка: BOT_TOKEN или CHAT_ID не настроены")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/getForumTopics"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"chat_id": chat_id}) as response:
            result = await response.json()
            
            if result.get("ok"):
                topics = result.get("result", [])
                print(f"📋 Найдено топиков: {len(topics)}")
                
                for topic in topics:
                    print(f"  • {topic.get('name', 'Без названия')} (ID: {topic.get('message_thread_id')})")
                    
                    # Ищем топик "АНОНСЫ ТРЕНИРОВОК"
                    if "анонс" in topic.get('name', '').lower() or "трениров" in topic.get('name', '').lower():
                        print(f"🎯 Найден топик 'АНОНСЫ ТРЕНИРОВОК': ID = {topic.get('message_thread_id')}")
                        return topic.get('message_thread_id')
            else:
                print(f"❌ Ошибка получения топиков: {result}")
    
    return None

async def send_to_topic(topic_id):
    """Отправляет сообщение в указанный топик"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Ошибка: BOT_TOKEN или CHAT_ID не настроены")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        print(f"📤 Отправляю сообщение в топик с ID: {topic_id}")
        
        message = await bot.send_message(
            chat_id=chat_id,
            text="🏀 Тестовое сообщение в топик 'АНОНСЫ ТРЕНИРОВОК'",
            message_thread_id=topic_id
        )
        
        print(f"✅ Сообщение отправлено! ID сообщения: {message.message_id}")
        print(f"🎯 ID топика 'АНОНСЫ ТРЕНИРОВОК': {topic_id}")
        print(f"\n📝 Добавьте в .env файл:")
        print(f"ANNOUNCEMENTS_TOPIC_ID={topic_id}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

async def main():
    """Основная функция"""
    
    print("🔍 Поиск топика 'АНОНСЫ ТРЕНИРОВОК'...")
    
    # Пытаемся найти топик автоматически
    topic_id = await get_forum_topics()
    
    if topic_id:
        print(f"\n✅ Топик найден! ID: {topic_id}")
        await send_to_topic(topic_id)
    else:
        print("\n❌ Топик 'АНОНСЫ ТРЕНИРОВОК' не найден автоматически")
        print("\n📝 Ручной способ:")
        print("1. Откройте чат с топиками")
        print("2. Найдите топик 'АНОНСЫ ТРЕНИРОВОК'")
        print("3. Отправьте любое сообщение от бота в этот топик")
        print("4. Проверьте обновления по ссылке:")
        
        bot_token = os.getenv('BOT_TOKEN')
        if bot_token:
            print(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        
        print("\n📋 В ответе найдите 'message_thread_id'")

if __name__ == "__main__":
    asyncio.run(main())
