#!/usr/bin/env python3
"""
Основной скрипт для запуска уведомлений о днях рождения
Используется в GitHub Actions или для ручного запуска
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
    
    if not bot_token:
        print("❌ BOT_TOKEN не настроен")
        return
    
    if not chat_id:
        print("❌ CHAT_ID не настроен")
        return
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    
    # Импортируем функцию проверки дней рождения
    from birthday_notifications import check_birthdays
    
    # Запускаем проверку дней рождения
    print("\n🔄 Запуск проверки дней рождения...")
    await check_birthdays()
    
    print("\n✅ Система уведомлений о днях рождения завершена")

if __name__ == "__main__":
    asyncio.run(main())
