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
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    print("🧪 ТЕСТ СОЗДАНИЯ ОПРОСА ТРЕНИРОВОК")
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
    
    # Варианты ответов для опроса тренировок
    training_options = [
        "🏀 Вторник 19:00",
        "🏀 Пятница 20:30",
        "👨‍🏫 Тренер",
        "❌ Нет"
    ]
    
    try:
        print("\n📤 Создаю опрос тренировок...")
        
        # Создаем опрос с множественным выбором в ТЕСТОВЫЙ канал
        poll = await bot.send_poll(
            chat_id=test_chat_id,
            question="🧪 ТЕСТ: Тренировки на неделе СШОР ВО",
            options=training_options,
            allows_multiple_answers=True,
            is_anonymous=False,  # Открытый опрос
            explanation="🧪 ТЕСТОВЫЙ ОПРОС - Выберите тренировки, на которые планируете прийти на этой неделе"
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
