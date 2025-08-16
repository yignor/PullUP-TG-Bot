#!/usr/bin/env python3
"""
Простой скрипт для отправки сообщения в топик с указанием ID
"""

import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def send_with_topic_id(topic_id):
    """Отправляет сообщение в указанный топик"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не настроены")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        print(f"📤 Отправляю сообщение в топик ID: {topic_id}")
        
        message = await bot.send_message(
            chat_id=chat_id,
            text="🏀 Тестовое сообщение от бота в топик 'АНОНСЫ ТРЕНИРОВОК'",
            message_thread_id=int(topic_id)
        )
        
        print(f"✅ Сообщение успешно отправлено!")
        print(f"📋 ID сообщения: {message.message_id}")
        print(f"\n🎯 ID топика найден: {topic_id}")
        print(f"📝 Добавьте в .env файл:")
        print(f"ANNOUNCEMENTS_TOPIC_ID={topic_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    """Основная функция"""
    
    print("🤖 ОТПРАВКА СООБЩЕНИЯ ОТ БОТА В ТОПИК")
    print("=" * 40)
    
    print("\n📋 Как найти ID топика:")
    print("1. Откройте чат с топиками в Telegram")
    print("2. Найдите топик 'АНОНСЫ ТРЕНИРОВОК'")
    print("3. ID топика обычно отображается в интерфейсе")
    print("4. Или попробуйте числа: 1, 2, 3, 4, 5...")
    
    # Попробуем несколько вариантов
    common_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    
    print(f"\n🔍 Попробую автоматически ID: {common_ids}")
    
    for topic_id in common_ids:
        success = await send_with_topic_id(topic_id)
        if success:
            break
    
    if not success:
        print("\n📝 Ручной ввод ID:")
        try:
            user_id = input("Введите ID топика (или Enter для пропуска): ").strip()
            if user_id:
                await send_with_topic_id(user_id)
        except KeyboardInterrupt:
            print("\n❌ Отменено пользователем")

if __name__ == "__main__":
    asyncio.run(main())
