#!/usr/bin/env python3
"""
Скрипт для запуска уведомлений о днях рождения в GitHub Actions
"""

import os
import asyncio
import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def main():
    """Основная функция для запуска уведомлений о днях рождения"""
    print("🎂 ЗАПУСК СИСТЕМЫ УВЕДОМЛЕНИЙ О ДНЯХ РОЖДЕНИЯ")
    print("=" * 60)
    
    # Показываем текущее время
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"🕐 Текущее время (Москва): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
    print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    
    # Дополнительная диагностика
    if google_credentials:
        print(f"🔍 GOOGLE_SHEETS_CREDENTIALS длина: {len(google_credentials)} символов")
        # Проверяем, что это валидный JSON
        try:
            import json
            json.loads(google_credentials)
            print("✅ GOOGLE_SHEETS_CREDENTIALS - валидный JSON")
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_SHEETS_CREDENTIALS - невалидный JSON: {e}")
        except Exception as e:
            print(f"❌ Ошибка проверки JSON: {e}")
    if spreadsheet_id:
        print(f"🔍 SPREADSHEET_ID: {spreadsheet_id}")
    
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
    
    # Импортируем функцию проверки дней рождения
    from birthday_notifications import check_birthdays
    
    # Запускаем проверку дней рождения
    print("\n🔄 Запуск проверки дней рождения...")
    print("=" * 60)
    
    await check_birthdays()
    
    print("=" * 60)
    print("\n✅ Система уведомлений о днях рождения завершена")

if __name__ == "__main__":
    asyncio.run(main())
