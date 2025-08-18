#!/usr/bin/env python3
"""Отправка уведомления об ошибке теста"""

import os
import asyncio
from telegram import Bot

async def send_failure_notification():
    """Отправляет уведомление об ошибке теста"""
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if bot_token and chat_id:
        bot = Bot(token=bot_token)
        message = """❌ ТЕСТ СИСТЕМЫ ДНЕЙ РОЖДЕНИЯ ПРОВАЛЕН

🔧 Проверьте логи в GitHub Actions для подробностей"""
        
        await bot.send_message(chat_id=chat_id, text=message)
        print("❌ Уведомление об ошибке теста отправлено")
    else:
        print("⚠️ Не удалось отправить уведомление - отсутствуют переменные окружения")

if __name__ == "__main__":
    asyncio.run(send_failure_notification())
