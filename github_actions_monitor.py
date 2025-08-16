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
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from telegram import Bot as BotType
from bs4 import BeautifulSoup
from pullup_notifications import PullUPNotificationManager

# Загружаем переменные окружения
load_dotenv()

# Настройки для продакшн и тестового чатов
BOT_TOKEN = os.getenv('BOT_TOKEN')
PROD_CHAT_ID = os.getenv('CHAT_ID')
TEST_CHAT_ID = os.getenv('TEST_CHAT_ID', '-15573582')

# Проверяем наличие обязательных переменных
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен")
    print("Установите переменную окружения BOT_TOKEN или добавьте её в .env файл")
    sys.exit(1)

if not PROD_CHAT_ID:
    print("❌ ОШИБКА: CHAT_ID не установлен")
    print("Установите переменную окружения CHAT_ID или добавьте её в .env файл")
    sys.exit(1)

# Type assertion to ensure BOT_TOKEN is a string
assert BOT_TOKEN is not None, "BOT_TOKEN should not be None after validation"
BOT_TOKEN_STR: str = BOT_TOKEN

async def send_github_error_notification(error_message: str, bot: Bot) -> None:
    """Отправляет уведомление об ошибке в тестовый чат"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_text = f"❌ ОШИБКА В GITHUB ACTIONS\n\n⏰ Время: {timestamp}\n\n🔍 Ошибка:\n{error_message}"
        
        await bot.send_message(chat_id=TEST_CHAT_ID, text=error_text)
        print(f"✅ Уведомление об ошибке отправлено в тестовый чат")
    except Exception as e:
        print(f"❌ Не удалось отправить уведомление об ошибке: {e}")

async def send_start_notification(bot: Bot) -> None:
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
    
    # Инициализируем бота
    bot: Bot = Bot(token=BOT_TOKEN_STR)
    
    try:
        print(f"✅ Бот инициализирован")
        print(f"🏭 Продакшн чат: {PROD_CHAT_ID}")
        print(f"🧪 Тестовый чат: {TEST_CHAT_ID}")
        
        # Уведомление о запуске убрано - отправляем только ошибки
        
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
            await send_github_error_notification(error_msg, bot)
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
                await send_github_error_notification(error_msg, bot)
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
                    await send_github_error_notification(error_msg, bot)
        else:
            print("ℹ️ Завершенных игр не найдено")
        
        # Уведомление об успешном завершении убрано - отправляем только ошибки
        print("✅ GitHub Actions завершен успешно")
        
    except Exception as e:
        error_message = f"Критическая ошибка в GitHub Actions:\n{str(e)}\n\nПолная трассировка:\n{traceback.format_exc()}"
        print(f"❌ Критическая ошибка: {e}")
        
        try:
            # Use the global function explicitly
            await send_github_error_notification(error_message, bot)
        except Exception as send_error:
            print(f"❌ Не удалось отправить уведомление об ошибке: {send_error}")
        
        # Выходим с ошибкой для GitHub Actions
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
