#!/usr/bin/env python3
"""
Скрипт для получения списка всех топиков в чате
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def get_all_topics():
    """Получает список всех топиков в чате"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    print("🔍 Получение списка всех топиков...")
    print(f"📋 Chat ID: {chat_id}")
    
    # Попробуем несколько методов API
    methods = [
        "getForumTopics",
        "getChat",
        "getChatMember"
    ]
    
    for method in methods:
        print(f"\n📡 Пробую метод: {method}")
        
        url = f"https://api.telegram.org/bot{bot_token}/{method}"
        
        if method == "getForumTopics":
            data = {"chat_id": chat_id}
        elif method == "getChat":
            data = {"chat_id": chat_id}
        elif method == "getChatMember":
            data = {"chat_id": chat_id, "user_id": bot_token.split(':')[0]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                
                if result.get("ok"):
                    print(f"✅ Метод {method} работает")
                    
                    if method == "getForumTopics":
                        topics = result.get("result", [])
                        print(f"📋 Найдено топиков: {len(topics)}")
                        
                        for i, topic in enumerate(topics):
                            name = topic.get('name', 'Без названия')
                            topic_id = topic.get('message_thread_id')
                            print(f"  {i+1}. {name} (ID: {topic_id})")
                            
                            # Ищем топик с ключевыми словами
                            if any(keyword in name.lower() for keyword in ['анонс', 'трениров', 'announce']):
                                print(f"    🎯 ВОЗМОЖНО ЭТО НУЖНЫЙ ТОПИК!")
                    
                    elif method == "getChat":
                        chat_info = result.get("result", {})
                        print(f"📋 Информация о чате:")
                        print(f"  Название: {chat_info.get('title', 'Неизвестно')}")
                        print(f"  Тип: {chat_info.get('type', 'Неизвестно')}")
                        print(f"  Форум: {chat_info.get('is_forum', False)}")
                        
                        if chat_info.get('is_forum'):
                            print("✅ Это форум с топиками")
                        else:
                            print("❌ Это не форум")
                
                else:
                    print(f"❌ Метод {method}: {result.get('description', 'Ошибка')}")

async def try_different_topic_ids():
    """Пробует отправить сообщения в разные топики"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    from telegram import Bot
    bot = Bot(token=bot_token)
    
    print("\n🔍 Попытка отправки в разные топики...")
    
    # Попробуем больше ID топиков
    possible_ids = list(range(1, 51))  # 1-50
    
    for topic_id in possible_ids:
        try:
            print(f"📤 Пробую топик ID: {topic_id}")
            
            message = await bot.send_message(
                chat_id=chat_id,
                text=f"🔍 Тест топика {topic_id}",
                message_thread_id=topic_id
            )
            
            print(f"✅ Успешно отправлено в топик ID: {topic_id}")
            print(f"📋 ID сообщения: {message.message_id}")
            
            # Спросим пользователя
            print(f"\n❓ Это правильный топик 'АНОНСЫ ТРЕНИРОВОК'? (y/n): ", end="")
            
            # В реальности здесь нужно было бы ждать ввода, но в автоматическом режиме просто продолжаем
            print("Проверьте сообщение в чате")
            
            return topic_id
            
        except Exception as e:
            error_msg = str(e)
            if "Message thread not found" in error_msg:
                print(f"❌ Топик {topic_id} не найден")
            else:
                print(f"❌ Топик {topic_id}: {error_msg[:50]}...")
            continue
    
    print("\n❌ Не удалось найти правильный топик")

if __name__ == "__main__":
    asyncio.run(get_all_topics())
    # asyncio.run(try_different_topic_ids())
