#!/usr/bin/env python3
"""
Тестовый скрипт для проверки нового токена
"""
import sys
import os
sys.path.append('..')

import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_new_token():
    """Тестирует новый токен"""
    print("🔑 ТЕСТИРОВАНИЕ НОВОГО ТОКЕНА")
    print("=" * 50)
    
    # Проверяем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token:
        print("❌ BOT_TOKEN не настроен в переменных окружения")
        print("В GitHub Actions токен должен быть в секретах")
        return
    
    if not chat_id:
        print("❌ CHAT_ID не настроен в переменных окружения")
        print("В GitHub Actions CHAT_ID должен быть в секретах")
        return
    
    print(f"✅ BOT_TOKEN найден (длина: {len(bot_token)})")
    print(f"✅ CHAT_ID найден: {chat_id}")
    print(f"Первые 10 символов токена: {bot_token[:10]}...")
    
    # Проверяем, не старый ли это токен
    if bot_token.startswith("7772125141"):
        print("⚠️ ВНИМАНИЕ: Используется старый токен!")
        print("Обновите BOT_TOKEN в GitHub Secrets")
        return
    
    try:
        # Создаем бота
        bot = Bot(token=bot_token)
        print("✅ Бот создан успешно")
        
        # Отправляем тестовое сообщение
        test_message = "🧪 ТЕСТ НОВОГО ТОКЕНА\n\n✅ Система работает с новым токеном!\n\n🕐 Время: " + str(asyncio.get_event_loop().time())
        
        await bot.send_message(chat_id=chat_id, text=test_message)
        print("✅ Тестовое сообщение отправлено успешно!")
        print("🎉 НОВЫЙ ТОКЕН РАБОТАЕТ КОРРЕКТНО!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании токена: {e}")
        if "Unauthorized" in str(e):
            print("🔍 Проблема: Токен не авторизован")
            print("Возможные причины:")
            print("1. Токен не обновлен в GitHub Secrets")
            print("2. Старый токен все еще используется")
            print("3. Токен неверный")
        elif "Chat not found" in str(e):
            print("🔍 Проблема: Чат не найден")
            print("Проверьте CHAT_ID в GitHub Secrets")
        else:
            print("🔍 Неизвестная ошибка")
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    asyncio.run(test_new_token())
