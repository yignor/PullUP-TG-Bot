#!/usr/bin/env python3
"""
Скрипт для проверки обновлений и поиска ID топика
"""

import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class BotWrapper:
    """Обертка для бота для решения проблем с типизацией"""
    
    def __init__(self, bot_instance):
        self._bot = bot_instance
    
    async def send_message(self, **kwargs):
        return await self._bot.send_message(**kwargs)

async def check_updates():
    """Проверяет обновления бота"""
    
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    print("🔍 Проверяю обновления бота...")
    print(f"🔗 URL: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            
            if result.get("ok"):
                updates = result.get("result", [])
                print(f"\n📋 Найдено обновлений: {len(updates)}")
                
                if not updates:
                    print("❌ Обновлений нет")
                    print("📝 Отправьте сообщение от бота в топик и попробуйте снова")
                    return
                
                for i, update in enumerate(updates):
                    print(f"\n📄 Обновление {i+1}:")
                    
                    if "message" in update:
                        message = update["message"]
                        
                        # Проверяем наличие message_thread_id
                        if "message_thread_id" in message:
                            topic_id = message["message_thread_id"]
                            text = message.get("text", "Нет текста")
                            chat_title = message.get("chat", {}).get("title", "Неизвестный чат")
                            
                            print(f"  ✅ Найден топик!")
                            print(f"  📋 ID топика: {topic_id}")
                            print(f"  💬 Текст: {text}")
                            print(f"  📱 Чат: {chat_title}")
                            
                            # Проверяем, похоже ли на нужный топик
                            if "анонс" in text.lower() or "трениров" in text.lower():
                                print(f"  🎯 ВОЗМОЖНО ЭТО НУЖНЫЙ ТОПИК!")
                            
                            print(f"\n📝 Добавьте в .env:")
                            print(f"ANNOUNCEMENTS_TOPIC_ID={topic_id}")
                            
                        else:
                            print(f"  ❌ Нет message_thread_id")
                            print(f"  💬 Текст: {message.get('text', 'Нет текста')}")
                            print(f"  📱 Чат: {message.get('chat', {}).get('title', 'Неизвестный чат')}")
                    
                    elif "channel_post" in update:
                        print(f"  📢 Канальное сообщение")
                    
                    else:
                        print(f"  ❓ Неизвестный тип обновления")
                
            else:
                print(f"❌ Ошибка: {result}")

async def send_and_check():
    """Отправляет сообщение и проверяет обновления"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    from telegram import Bot
    
    # Создаем экземпляр бота и обертку
    bot_instance = Bot(token=bot_token)
    bot_wrapper = BotWrapper(bot_instance)
    
    print("📤 Отправляю тестовое сообщение...")
    
    try:
        # Отправляем сообщение в общий чат
        message = await bot_wrapper.send_message(
            chat_id=chat_id,
            text="🔍 Тестовое сообщение для поиска ID топика"
        )
        
        print(f"✅ Сообщение отправлено! ID: {message.message_id}")
        print("\n📝 Теперь:")
        print("1. Перейдите в чат")
        print("2. Переместите это сообщение в топик 'АНОНСЫ ТРЕНИРОВОК'")
        print("3. Или отправьте новое сообщение от бота прямо в топик")
        print("4. Затем нажмите Enter для проверки обновлений...")
        
        input("Нажмите Enter для проверки обновлений...")
        
        await check_updates()
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--send":
        asyncio.run(send_and_check())
    else:
        asyncio.run(check_updates())
