#!/usr/bin/env python3
"""
Скрипт для тестирования отправки уведомления о дне рождения
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from birthday_bot_simple import get_years_word

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

async def test_birthday_notification():
    """Тестирует отправку уведомления о дне рождения"""
    print("\n=== ТЕСТИРОВАНИЕ УВЕДОМЛЕНИЯ О ДНЕ РОЖДЕНИЯ ===\n")
    
    success, bot_token, chat_id = load_env_variables()
    if not success:
        return
    
    try:
        bot = Bot(token=bot_token)
        print("✅ Бот инициализирован")
        
        # Симулируем именинника
        test_birthday_people = [
            "Шахманов Максим (19 лет)",
            "Хан Александр (31 год)"
        ]
        
        print(f"1. Отправка уведомления о дне рождения...")
        text = "🎉 Сегодня день рождения у " + ", ".join(test_birthday_people) + "! \n Поздравляем! 🎂"
        
        await bot.send_message(chat_id=chat_id, text=text)
        print("✅ Уведомление о дне рождения отправлено!")
        print(f"   Сообщение: {text}")
        
        # Тестируем опрос для поздравления
        print(f"\n2. Тестирование создания опроса для поздравления...")
        
        question = f"🎂 Как поздравить {test_birthday_people[0]} с днем рождения?"
        options = [
            "🎉 Поздравление в чате",
            "🎵 Музыкальное поздравление",
            "🏀 Баскетбольное поздравление",
            "🎁 Подарок команде",
            "🍰 Торт и праздник"
        ]
        
        # Создаем опрос
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
        print("✅ Опрос для поздравления создан!")
        print(f"   Вопрос: {question}")
        print(f"   Варианты: {', '.join(options)}")
        
        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
        print("📋 Проверьте Telegram чат для подтверждения")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_birthday_notification())
