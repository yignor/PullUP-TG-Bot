#!/usr/bin/env python3
"""
Скрипт для запуска системы опросов тренировок в GitHub Actions
"""

import os
import asyncio
import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def main():
    """Основная функция для запуска системы опросов тренировок"""
    print("🏀 ЗАПУСК СИСТЕМЫ ОПРОСОВ ТРЕНИРОВОК")
    print("=" * 60)
    
    # Показываем текущее время
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 День недели: {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][now.weekday()]}")
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    announcements_topic_id = os.getenv("ANNOUNCEMENTS_TOPIC_ID", "26")
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
    print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    print(f"ANNOUNCEMENTS_TOPIC_ID: {announcements_topic_id}")
    
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not chat_id:
        print("❌ CHAT_ID не настроен")
        return
    
    if not google_credentials:
        print("❌ GOOGLE_SHEETS_CREDENTIALS не настроен")
        return
    
    if not spreadsheet_id:
        print("❌ SPREADSHEET_ID не настроен")
        return
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    print(f"✅ SPREADSHEET_ID: {spreadsheet_id}")
    print(f"✅ ANNOUNCEMENTS_TOPIC_ID: {announcements_topic_id}")
    
    # Импортируем функцию управления опросами тренировок
    from training_polls import main_training_polls
    
    # Запускаем систему опросов тренировок
    print("\n🔄 Запуск системы опросов тренировок...")
    await main_training_polls()
    
    print("\n✅ Система опросов тренировок завершена")

if __name__ == "__main__":
    asyncio.run(main())
