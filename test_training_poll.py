#!/usr/bin/env python3
"""
Тестовый скрипт для проверки создания опроса тренировок
"""

import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_training_poll():
    """Тестирует создание опроса тренировок"""
    
    # Получаем настройки
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    topic_id = os.getenv('ANNOUNCEMENTS_TOPIC_ID')
    
    print("🧪 ТЕСТ СОЗДАНИЯ ОПРОСА ТРЕНИРОВОК")
    print("=" * 40)
    
    # Проверяем настройки
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not chat_id:
        print("❌ CHAT_ID не настроен")
        return
    
    if not topic_id:
        print("❌ ANNOUNCEMENTS_TOPIC_ID не настроен")
        return
    
    print(f"✅ BOT_TOKEN: {'*' * 10}{bot_token[-4:]}")
    print(f"✅ CHAT_ID: {chat_id}")
    print(f"✅ ANNOUNCEMENTS_TOPIC_ID: {topic_id}")
    
    bot = Bot(token=bot_token)
    
    # Варианты ответов для опроса тренировок
    training_options = [
        "🏀 Вторник 19:00",
        "🏀 Пятница 20:30",
        "👨‍🏫 Тренер",
        "❌ Нет"
    ]
    
    try:
        print("\n📤 Создаю опрос тренировок...")
        
        # Создаем опрос с множественным выбором
        poll = await bot.send_poll(
            chat_id=chat_id,
            question="🏀 Тренировки на неделе СШОР ВО",
            options=training_options,
            allows_multiple_answers=True,
            is_anonymous=False,  # Открытый опрос
            explanation="Выберите тренировки, на которые планируете прийти на этой неделе",
            message_thread_id=int(topic_id)  # Отправляем в топик "АНОНСЫ ТРЕНИРОВОК"
        )
        
        print(f"✅ Опрос тренировок создан!")
        print(f"📋 ID сообщения: {poll.message_id}")
        print(f"📋 Вопрос: {poll.poll.question}")
        print(f"📋 Варианты: {len(poll.poll.options)}")
        print(f"📋 Время создания: {poll.date}")
        
        print("\n🎯 Система тренировок готова к работе!")
        print("📝 Опросы будут создаваться каждое воскресенье в 10:00 по Москве")
        
    except Exception as e:
        print(f"❌ Ошибка создания опроса: {e}")
        print("\n🔍 Возможные причины:")
        print("1. Неправильный ID топика")
        print("2. Бот не имеет прав на создание опросов")
        print("3. Бот не имеет прав на отправку в топик")

if __name__ == "__main__":
    asyncio.run(test_training_poll())
