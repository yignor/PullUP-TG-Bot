#!/usr/bin/env python3
"""
Скрипт для тестирования создания опроса по воскресеньям
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

def load_env_variables():
    """Загружает переменные из .env файла"""
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Переменные загружены из .env файла")
        except FileNotFoundError:
            print("❌ Файл .env не найден")
            return False, None, None
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False, None, None
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True, bot_token, chat_id

async def test_sunday_poll_creation():
    """Тестирует создание опроса по воскресеньям"""
    print("\n=== ТЕСТИРОВАНИЕ СОЗДАНИЯ ОПРОСА ПО ВОСКРЕСЕНЬЯМ ===\n")
    
    success, bot_token, chat_id = load_env_variables()
    if not success:
        return
    
    try:
        bot = Bot(token=bot_token)
        print("✅ Бот инициализирован")
        
        # Варианты ответов для опроса тренировок
        training_options = [
            "🏀 Вторник 19:00",
            "🏀 Пятница 20:30",
            "👨‍🏫 Тренер",
            "❌ Нет"
        ]
        
        print(f"1. Создание опроса тренировок на неделю...")
        question = "🏀 Тренировки на неделе СШОР ВО"
        
        # Создаем опрос с множественным выбором
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=training_options,
            allows_multiple_answers=True,
            is_anonymous=False,  # Открытый опрос
            explanation="Выберите тренировки, на которые планируете прийти на этой неделе"
        )
        
        print("✅ Опрос тренировок создан успешно!")
        print(f"   Вопрос: {poll.poll.question}")
        print(f"   Варианты: {poll.poll.options}")
        print(f"   Множественный выбор: {'Да' if poll.poll.allows_multiple_answers else 'Нет'}")
        print(f"   Анонимный: {'Нет' if poll.poll.is_anonymous else 'Да'}")
        
        # Тестируем создание мотивационного опроса
        print(f"\n2. Создание мотивационного опроса...")
        motivation_question = "💪 Что больше всего мотивирует команду PullUP?"
        motivation_options = [
            "🏆 Победы и трофеи",
            "👥 Командный дух",
            "🏀 Любовь к баскетболу",
            "💪 Физическая подготовка",
            "🎯 Цели и амбиции"
        ]
        
        motivation_poll = await bot.send_poll(
            chat_id=chat_id,
            question=motivation_question,
            options=motivation_options,
            allows_multiple_answers=False,
            is_anonymous=False,
            explanation="Помогите понять, что движет командой! 💪"
        )
        
        print("✅ Мотивационный опрос создан успешно!")
        print(f"   Вопрос: {motivation_poll.poll.question}")
        print(f"   Варианты: {motivation_poll.poll.options}")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте Telegram чат для подтверждения")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sunday_poll_creation())
