#!/usr/bin/env python3
"""
Обновленная версия birthday_bot.py с использованием Google Sheets
"""

import datetime
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv
from typing import Any

# Импортируем менеджер игроков
from players_manager import players_manager, get_years_word

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Инициализируем бота как None, будет создан при необходимости
bot: Any = None

def get_bot():
    """Получает инициализированного бота"""
    global bot
    if bot is None:
        try:
            if BOT_TOKEN:
                bot = Bot(token=BOT_TOKEN)
                print(f"✅ Бот инициализирован успешно")
            else:
                print("❌ BOT_TOKEN не настроен")
                return None
        except Exception as e:
            print(f"❌ ОШИБКА при инициализации бота: {e}")
            return None
    return bot

def get_moscow_time():
    """Возвращает текущее время в часовом поясе Москвы"""
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))  # UTC+3 для Москвы
    return datetime.datetime.now(moscow_tz)

def should_check_birthdays():
    """Проверяет, нужно ли проверять дни рождения (только в 9:00-9:29 по Москве)"""
    moscow_time = get_moscow_time()
    return moscow_time.hour == 9 and moscow_time.minute < 30

async def check_birthdays():
    """Проверяет дни рождения и отправляет уведомления"""
    try:
        # Проверяем время
        if not should_check_birthdays():
            print("⏰ Не время для проверки дней рождения (только 9:00-9:29 по Москве)")
            return
        
        print("🎂 Проверка дней рождения...")
        
        # Получаем игроков с днями рождения сегодня
        birthday_players = players_manager.get_players_with_birthdays_today()
        
        if birthday_players:
            # Формируем список именинников
            birthday_list = []
            for player in birthday_players:
                age = player.get('age', 0)
                years_word = get_years_word(age)
                birthday_list.append(f"{player['name']} ({age} {years_word})")
            
            # Отправляем уведомление
            text = "🎉 Сегодня день рождения у " + ", ".join(birthday_list) + "! \n Поздравляем! 🎂"
            
            current_bot = get_bot()
            if current_bot:
                await current_bot.send_message(chat_id=CHAT_ID, text=text)
                print("✅ Отправлено:", text)
            else:
                print("❌ Не удалось отправить уведомление - бот не инициализирован")
        else:
            print("📅 Сегодня нет дней рождения.")
            
    except Exception as e:
        print(f"❌ Ошибка проверки дней рождения: {e}")

async def test_birthday_system():
    """Тестирует систему дней рождения"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 50)
    
    # Проверяем подключение к Google Sheets
    if not players_manager.players_sheet:
        print("❌ Google Sheets не подключен")
        print("   Убедитесь, что настроены GOOGLE_SHEETS_CREDENTIALS и SPREADSHEET_ID")
        return
    
    print("✅ Google Sheets подключен")
    
    # Получаем всех игроков
    all_players = players_manager.get_all_players()
    print(f"📊 Всего игроков: {len(all_players)}")
    
    # Получаем активных игроков
    active_players = players_manager.get_active_players()
    print(f"✅ Активных игроков: {len(active_players)}")
    
    # Проверяем дни рождения сегодня
    birthday_players = players_manager.get_players_with_birthdays_today()
    print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
    
    if birthday_players:
        print("🎉 Именинники:")
        for player in birthday_players:
            age = player.get('age', 0)
            years_word = get_years_word(age)
            print(f"   - {player['name']} ({age} {years_word})")
    
    # Тестируем отправку уведомления
    print("\n📤 Тестирование отправки уведомления...")
    await check_birthdays()
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_birthday_system())
