#!/usr/bin/env python3
"""
Скрипт для отправки тестового анонса игры Визотек без топика
"""

import os
import asyncio
import datetime
from dotenv import load_dotenv

load_dotenv()

async def send_test_announcement():
    """Отправляет тестовый анонс игры Визотек"""
    print("📢 ОТПРАВКА ТЕСТОВОГО АНОНСА ИГРЫ ВИЗОТЕК (БЕЗ ТОПИКА)")
    print("=" * 60)
    
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")

    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")

    if not all([bot_token, chat_id]):
        print("❌ Не все переменные окружения настроены")
        return

    print(f"✅ CHAT_ID: {chat_id}")

    # Импортируем необходимые модули
    from telegram import Bot
    
    # Создаем экземпляр бота
    bot = Bot(token=bot_token)
    
    # Создаем тестовую информацию об игре Визотек
    test_game_info = {
        'team1': 'Визотек',
        'team2': 'Тестовая команда',
        'date': now.strftime('%d.%m.%Y'),
        'time': '20.30',
        'venue': 'ВО СШОР Малый 66'
    }
    
    # Ищем ссылку на игру
    print("\n🔍 Поиск ссылки на игру Визотек...")
    from game_day_announcer import GameDayAnnouncer
    announcer = GameDayAnnouncer()
    game_link = await announcer.find_game_link('Визотек', 'Тестовая команда')
    
    # Формируем анонс
    announcement_text = announcer.format_announcement_message(test_game_info, game_link)
    
    print(f"\n📢 ТЕСТОВЫЙ АНОНС:")
    print(announcement_text)
    
    # Отправляем сообщение без указания топика
    try:
        message = await bot.send_message(
            chat_id=int(chat_id),
            text=announcement_text,
            parse_mode='HTML'
        )
        
        print(f"✅ Тестовый анонс отправлен!")
        print(f"📊 ID сообщения: {message.message_id}")
        print(f"📅 Дата: {test_game_info['date']}")
        print(f"🕐 Время: {test_game_info['time']}")
        print(f"📍 Место: {test_game_info['venue']}")
        if game_link:
            print(f"🔗 Ссылка: {game_link}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки анонса: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_announcement())
