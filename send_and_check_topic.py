#!/usr/bin/env python3
"""
Скрипт для отправки сообщения в топик и проверки обновлений
"""

import os
import asyncio
import aiohttp
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def send_to_topic_and_check():
    """Отправляет сообщение в топик и проверяет обновления"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    bot = Bot(token=bot_token)
    
    print("📤 Отправляю сообщение прямо в топик 'АНОНСЫ ТРЕНИРОВОК'...")
    print("📝 Пожалуйста, убедитесь, что бот имеет права на отправку в топики")
    
    # Попробуем несколько возможных ID топиков
    possible_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    
    for topic_id in possible_ids:
        try:
            print(f"\n🔍 Пробую топик ID: {topic_id}")
            
            message = await bot.send_message(
                chat_id=chat_id,
                text=f"🏀 Тестовое сообщение в топик (ID: {topic_id})",
                message_thread_id=topic_id
            )
            
            print(f"✅ Успешно отправлено в топик ID: {topic_id}")
            print(f"📋 ID сообщения: {message.message_id}")
            
            # Сразу проверяем обновления
            print("\n🔍 Проверяю обновления...")
            await check_updates_for_topic(topic_id)
            
            return topic_id
            
        except Exception as e:
            print(f"❌ Топик ID {topic_id}: {str(e)[:50]}...")
            continue
    
    print("\n❌ Не удалось найти правильный ID топика")
    print("📝 Попробуйте ручной способ или проверьте права бота")

async def check_updates_for_topic(expected_topic_id):
    """Проверяет обновления для конкретного топика"""
    
    bot_token = os.getenv('BOT_TOKEN')
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            
            if result.get("ok"):
                updates = result.get("result", [])
                print(f"📋 Найдено обновлений: {len(updates)}")
                
                for update in updates:
                    if "message" in update:
                        message = update["message"]
                        
                        if "message_thread_id" in message:
                            topic_id = message["message_thread_id"]
                            text = message.get("text", "Нет текста")
                            
                            print(f"✅ Найден топик ID: {topic_id}")
                            print(f"💬 Текст: {text}")
                            
                            if topic_id == expected_topic_id:
                                print(f"🎯 ЭТО ПРАВИЛЬНЫЙ ТОПИК!")
                                print(f"📝 Добавьте в .env:")
                                print(f"ANNOUNCEMENTS_TOPIC_ID={topic_id}")
                                return topic_id
                            else:
                                print(f"📝 Альтернативный ID топика: {topic_id}")
                
            else:
                print(f"❌ Ошибка: {result}")

if __name__ == "__main__":
    asyncio.run(send_to_topic_and_check())
