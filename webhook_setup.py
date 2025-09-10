#!/usr/bin/env python3
"""
Настройка webhook для получения всех обновлений в реальном времени
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

async def setup_webhook():
    """Настройка webhook для получения всех обновлений"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    print("🔧 НАСТРОЙКА WEBHOOK ДЛЯ ПОЛУЧЕНИЯ ВСЕХ ОБНОВЛЕНИЙ")
    print("=" * 60)
    
    # Получаем текущую информацию о webhook
    webhook_info = await bot.get_webhook_info()
    print(f"📊 Текущий webhook URL: {webhook_info.url}")
    print(f"📊 Необработанных обновлений: {webhook_info.pending_update_count}")
    
    if webhook_info.url:
        print("⚠️ Webhook уже настроен!")
        print("🔄 Удаляем текущий webhook...")
        try:
            await bot.delete_webhook()
            print("✅ Webhook удален")
        except Exception as e:
            print(f"❌ Ошибка удаления webhook: {e}")
    
    # Очищаем все необработанные обновления
    if webhook_info.pending_update_count > 0:
        print(f"🔄 Очищаем {webhook_info.pending_update_count} необработанных обновлений...")
        try:
            updates = await bot.get_updates(limit=1000, timeout=30)
            print(f"✅ Получено и очищено {len(updates)} обновлений")
        except Exception as e:
            print(f"❌ Ошибка очистки обновлений: {e}")
    
    print("\n📋 ИНСТРУКЦИИ ДЛЯ НАСТРОЙКИ WEBHOOK:")
    print("=" * 50)
    print("1. Для получения всех обновлений в реальном времени нужно настроить webhook")
    print("2. Webhook должен быть доступен по HTTPS")
    print("3. Можно использовать ngrok для локальной разработки:")
    print("   - Установите ngrok: https://ngrok.com/")
    print("   - Запустите: ngrok http 8080")
    print("   - Используйте полученный URL для webhook")
    print("4. Или используйте облачный сервис (Heroku, Railway, etc.)")
    print("\n🔧 КОМАНДЫ ДЛЯ НАСТРОЙКИ WEBHOOK:")
    print("=" * 50)
    print("# Установить webhook (замените YOUR_WEBHOOK_URL на ваш URL):")
    print("await bot.set_webhook(url='YOUR_WEBHOOK_URL')")
    print("\n# Проверить webhook:")
    print("webhook_info = await bot.get_webhook_info()")
    print("print(f'Webhook URL: {webhook_info.url}')")
    print("print(f'Pending updates: {webhook_info.pending_update_count}')")
    
    print("\n⚠️ ВАЖНО:")
    print("=" * 50)
    print("• Без webhook бот может получать только ограниченное количество обновлений")
    print("• Старые голоса (более 24 часов) могут быть недоступны")
    print("• Рекомендуется собирать данные опроса сразу после его создания")
    print("• Для текущего опроса можно использовать ручной ввод данных")
    
    print("\n🔧 ВРЕМЕННОЕ РЕШЕНИЕ:")
    print("=" * 50)
    print("1. Запустите manual_poll_data.py для ручного ввода данных")
    print("2. Или используйте webhook_solution.py для получения доступных обновлений")
    print("3. Настройте webhook для будущих опросов")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
