#!/usr/bin/env python3
"""
Альтернативные способы получения данных опроса
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

async def try_alternative_methods():
    """Пробуем альтернативные способы получения данных опроса"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найден")
        return
    
    bot = Bot(token=bot_token)
    
    print("🔍 АЛЬТЕРНАТИВНЫЕ СПОСОБЫ ПОЛУЧЕНИЯ ДАННЫХ ОПРОСА")
    print("=" * 60)
    
    # Метод 1: Попробуем получить информацию о чате
    try:
        print("\n📊 Метод 1: Информация о чате")
        chat = await bot.get_chat(chat_id)
        print(f"   Название чата: {chat.title}")
        print(f"   Тип чата: {chat.type}")
        print(f"   Количество участников: {chat.member_count if hasattr(chat, 'member_count') else 'Неизвестно'}")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения информации о чате: {e}")
    
    # Метод 2: Попробуем получить администраторов
    try:
        print("\n📊 Метод 2: Администраторы чата")
        admins = await bot.get_chat_administrators(chat_id)
        print(f"   Количество администраторов: {len(admins)}")
        for admin in admins[:3]:  # Показываем первых 3
            print(f"   - {admin.user.first_name} {admin.user.last_name or ''}")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения администраторов: {e}")
    
    # Метод 3: Попробуем получить участников чата
    try:
        print("\n📊 Метод 3: Участники чата")
        members = await bot.get_chat_member_count(chat_id)
        print(f"   Количество участников: {members}")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения количества участников: {e}")
    
    # Метод 4: Попробуем получить историю сообщений
    try:
        print("\n📊 Метод 4: История сообщений")
        # Это может не работать для больших чатов
        print("   ⚠️ get_chat_history недоступен в python-telegram-bot")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения истории: {e}")
    
    # Метод 5: Попробуем использовать webhook (если настроен)
    try:
        print("\n📊 Метод 5: Webhook информация")
        webhook_info = await bot.get_webhook_info()
        print(f"   URL webhook: {webhook_info.url}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")
        if webhook_info.pending_update_count > 0:
            print(f"   ⚠️ Есть {webhook_info.pending_update_count} необработанных обновлений!")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения информации о webhook: {e}")
    
    # Метод 6: Попробуем получить обновления с очень большим offset
    try:
        print("\n📊 Метод 6: Обновления с большим offset")
        # Пробуем получить обновления с очень большим отрицательным offset
        for offset in [-50000, -100000, -200000]:
            updates = await bot.get_updates(limit=1000, offset=offset, timeout=5)
            if updates:
                poll_answers = sum(1 for u in updates if u.poll_answer)
                print(f"   Offset {offset}: {len(updates)} обновлений, {poll_answers} голосов")
                if poll_answers > 0:
                    print(f"   ✅ Найдены голоса с offset {offset}")
                    break
            else:
                print(f"   Offset {offset}: нет обновлений")
    except Exception as e:
        print(f"   ⚠️ Ошибка получения обновлений с большим offset: {e}")

if __name__ == "__main__":
    asyncio.run(try_alternative_methods())
