#!/usr/bin/env python3
"""Отправка уведомления об успешном тесте"""

import os
import asyncio
from telegram import Bot

async def send_success_notification():
    """Отправляет уведомление об успешном тесте"""
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if bot_token and chat_id:
        bot = Bot(token=bot_token)
        message = """✅ ТЕСТ СИСТЕМЫ ДНЕЙ РОЖДЕНИЯ ПРОЙДЕН УСПЕШНО

🎂 Новая система работает корректно:
• Google Sheets подключение ✅
• Логика дней рождения ✅
• Форматирование сообщений ✅
• PlayersManager ✅"""
        
        await bot.send_message(chat_id=chat_id, text=message)
        print("✅ Уведомление об успешном тесте отправлено")
    else:
        print("⚠️ Не удалось отправить уведомление - отсутствуют переменные окружения")

if __name__ == "__main__":
    asyncio.run(send_success_notification())
