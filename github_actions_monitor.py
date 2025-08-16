#!/usr/bin/env python3
"""
Скрипт для запуска в GitHub Actions с отправкой ошибок в тестовый чат
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from bs4 import BeautifulSoup
from pullup_notifications import PullUPNotificationManager

# Загружаем переменные окружения
load_dotenv()

# Настройки для продакшн и тестового чатов
BOT_TOKEN = os.getenv('BOT_TOKEN', '7772125141:AAHqFYGm3I6MW516aCq3K0FFjK2EGKk0wtw')
PROD_CHAT_ID = os.getenv('CHAT_ID', '-1001535261616')
TEST_CHAT_ID = os.getenv('TEST_CHAT_ID', '-15573582')

async def send_error_notification(error_message, bot):
    """Отправляет уведомление об ошибке в тестовый чат"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_text = f"❌ ОШИБКА В GITHUB ACTIONS\n\n⏰ Время: {timestamp}\n\n🔍 Ошибка:\n{error_message}"
        
        await bot.send_message(chat_id=TEST_CHAT_ID, text=error_text)
        print(f"✅ Уведомление об ошибке отправлено в тестовый чат")
    except Exception as e:
        print(f"❌ Не удалось отправить уведомление об ошибке: {e}")

async def send_start_notification(bot):
    """Отправляет уведомление о начале работы в тестовый чат"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_text = f"🚀 GITHUB ACTIONS ЗАПУЩЕН\n\n⏰ Время: {timestamp}\n🏭 Продакшн чат: {PROD_CHAT_ID}\n🧪 Тестовый чат: {TEST_CHAT_ID}"
        
        await bot.send_message(chat_id=TEST_CHAT_ID, text=start_text)
        print(f"✅ Уведомление о запуске отправлено в тестовый чат")
    except Exception as e:
        print(f"❌ Не удалось отправить уведомление о запуске: {e}")

async def main():
    """Основная функция для GitHub Actions"""
    print("🚀 Запуск GitHub Actions монитора...")
    
    try:
        # Инициализируем бота
        bot = Bot(token=BOT_TOKEN)
        print(f"✅ Бот инициализирован")
        print(f"🏭 Продакшн чат: {PROD_CHAT_ID}")
        print(f"🧪 Тестовый чат: {TEST_CHAT_ID}")
        
        # Отправляем уведомление о запуске
        await send_start_notification(bot)
        
        # Инициализируем менеджер уведомлений
        manager = PullUPNotificationManager()
        print("✅ Менеджер уведомлений инициализирован")
        
        # Получаем свежий контент
        print("\n1. Получение данных с сайта...")
        html_content = await manager.get_fresh_page_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        
        # Извлекаем текущую дату
        current_date = manager.extract_current_date(page_text)
        if not current_date:
            error_msg = "Не удалось извлечь текущую дату"
            await send_error_notification(error_msg, bot)
            return
        
        print(f"✅ Текущая дата: {current_date}")
        
        # Проверяем предстоящие игры
        print("\n2. Проверка предстоящих игр...")
        pullup_games = manager.find_pullup_games(page_text, current_date)
        
        if pullup_games:
            print(f"✅ Найдено {len(pullup_games)} предстоящих игр")
            try:
                await manager.send_morning_notification(pullup_games, html_content)
                print(f"✅ Уведомление о предстоящих играх отправлено")
            except Exception as e:
                error_msg = f"Ошибка отправки уведомления о предстоящих играх: {str(e)}\nИгры: {pullup_games}"
                await send_error_notification(error_msg, bot)
        else:
            print("ℹ️ Предстоящих игр не найдено")
        
        # Проверяем завершенные игры
        print("\n3. Проверка завершенных игр...")
        finished_games = manager.check_finished_games(html_content, current_date)
        
        if finished_games:
            print(f"✅ Найдено {len(finished_games)} завершенных игр")
            for game in finished_games:
                try:
                    await manager.send_finish_notification(game)
                    print(f"✅ Уведомление о завершенной игре отправлено")
                except Exception as e:
                    error_msg = f"Ошибка отправки уведомления о завершенной игре: {str(e)}\nИгра: {game}"
                    await send_error_notification(error_msg, bot)
        else:
            print("ℹ️ Завершенных игр не найдено")
        
        # Отправляем уведомление об успешном завершении
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_text = f"✅ GITHUB ACTIONS ЗАВЕРШЕН УСПЕШНО\n\n⏰ Время: {timestamp}\n📊 Предстоящих игр: {len(pullup_games) if pullup_games else 0}\n🏁 Завершенных игр: {len(finished_games) if finished_games else 0}"
        
        await bot.send_message(chat_id=TEST_CHAT_ID, text=success_text)
        print("✅ Уведомление об успешном завершении отправлено")
        
    except Exception as e:
        error_message = f"Критическая ошибка в GitHub Actions:\n{str(e)}\n\nПолная трассировка:\n{traceback.format_exc()}"
        print(f"❌ Критическая ошибка: {e}")
        
        try:
            await send_error_notification(error_message, bot)
        except Exception as send_error:
            print(f"❌ Не удалось отправить уведомление об ошибке: {send_error}")
        
        # Выходим с ошибкой для GitHub Actions
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
