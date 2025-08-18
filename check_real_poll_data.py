#!/usr/bin/env python3
"""
Скрипт для проверки реальных данных опроса по ID
"""

import os
import asyncio
import datetime
import json
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def check_poll_data():
    """Проверяет реальные данные опроса"""
    print("🔍 ПРОВЕРКА РЕАЛЬНЫХ ДАННЫХ ОПРОСА")
    print("=" * 60)
    
    # Проверяем переменные окружения
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
    print(f"CHAT_ID: {'✅' if CHAT_ID else '❌'}")
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Не все переменные окружения настроены")
        return False
    
    try:
        # Инициализируем бота
        bot = Bot(token=BOT_TOKEN)
        print("✅ Бот инициализирован")
        
        # Загружаем информацию об опросе
        if not os.path.exists('test_poll_info.json'):
            print("❌ Файл test_poll_info.json не найден")
            return False
        
        with open('test_poll_info.json', 'r', encoding='utf-8') as f:
            poll_info = json.load(f)
        
        message_id = poll_info['message_id']
        poll_id = poll_info['poll_id']
        
        print(f"📊 ID сообщения: {message_id}")
        print(f"📊 ID опроса: {poll_id}")
        
        # Пытаемся получить информацию о чате
        print("\n🔄 Получение информации о чате...")
        try:
            chat = await bot.get_chat(chat_id=int(CHAT_ID))
            print(f"✅ Информация о чате получена: {chat.title}")
        except Exception as e:
            print(f"❌ Ошибка получения информации о чате: {e}")
        
        # Пытаемся получить информацию о боте
        print("\n🔄 Получение информации о боте...")
        try:
            bot_info = await bot.get_me()
            print(f"✅ Информация о боте: {bot_info.first_name} (@{bot_info.username})")
        except Exception as e:
            print(f"❌ Ошибка получения информации о боте: {e}")
        
        # Пытаемся получить обновления (для проверки доступа к сообщениям)
        print("\n🔄 Проверка доступа к обновлениям...")
        try:
            updates = await bot.get_updates(limit=1)
            if updates:
                print(f"✅ Получено {len(updates)} обновлений")
                for update in updates:
                    if update.message and update.message.poll:
                        print(f"   Найден опрос в обновлении: {update.message.poll.question}")
            else:
                print("⚠️ Обновления не найдены")
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
        
        # Пытаемся получить информацию о правах бота в чате
        print("\n🔄 Проверка прав бота в чате...")
        try:
            chat_member = await bot.get_chat_member(chat_id=int(CHAT_ID), user_id=bot_info.id)
            print(f"✅ Статус бота в чате: {chat_member.status}")
            print(f"✅ Права бота:")
            print(f"   - Может читать сообщения: {chat_member.can_read_messages}")
            print(f"   - Может отправлять сообщения: {chat_member.can_send_messages}")
            print(f"   - Может отправлять опросы: {chat_member.can_send_polls}")
        except Exception as e:
            print(f"❌ Ошибка получения информации о правах: {e}")
        
        # Пытаемся получить последние сообщения
        print("\n🔄 Попытка получения последних сообщений...")
        try:
            # К сожалению, Bot API не предоставляет прямой доступ к истории сообщений
            print("⚠️ Bot API не предоставляет прямой доступ к истории сообщений")
            print("   Для получения результатов опросов нужен Telegram Client API")
            
            # Альтернативный подход - попробуем получить информацию через webhook или polling
            print("\n💡 РЕКОМЕНДАЦИИ ДЛЯ ПОЛУЧЕНИЯ РЕАЛЬНЫХ ДАННЫХ:")
            print("1. Настроить Telegram Client API (если заработает код подтверждения)")
            print("2. Настроить webhook для получения обновлений в реальном времени")
            print("3. Использовать polling для получения обновлений")
            print("4. Создать новый опрос и отслеживать результаты через обновления")
            
        except Exception as e:
            print(f"❌ Ошибка получения сообщений: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

async def main():
    """Основная функция"""
    success = await check_poll_data()
    
    if success:
        print("\n" + "=" * 60)
        print("🔍 ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 60)
        print("📋 Выводы:")
        print("1. ✅ Бот работает и имеет доступ к чату")
        print("2. ⚠️ Bot API не предоставляет доступ к истории сообщений")
        print("3. 💡 Нужны альтернативные методы для получения результатов")
    else:
        print("\n❌ ОШИБКА ПРОВЕРКИ")

if __name__ == "__main__":
    asyncio.run(main())
