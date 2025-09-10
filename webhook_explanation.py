#!/usr/bin/env python3
"""
Объяснение работы webhook и автоматическая настройка
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

async def explain_webhook():
    """Объяснение работы webhook"""
    
    print("🔧 КАК РАБОТАЕТ WEBHOOK")
    print("=" * 50)
    
    print("📊 ТЕКУЩИЙ ПОДХОД (get_updates):")
    print("1. Бот запрашивает обновления: bot.get_updates()")
    print("2. Telegram возвращает только последние N обновлений")
    print("3. Старые обновления могут быть недоступны")
    print("4. Нужно постоянно опрашивать сервер")
    
    print("\n📊 WEBHOOK ПОДХОД:")
    print("1. Бот регистрирует URL: bot.set_webhook(url='https://yourserver.com/webhook')")
    print("2. Telegram отправляет обновления на ваш сервер в реальном времени")
    print("3. Ваш сервер получает ВСЕ обновления сразу")
    print("4. Никаких ограничений по количеству или времени")
    
    print("\n🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА WEBHOOK:")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    # Проверяем текущий webhook
    webhook_info = await bot.get_webhook_info()
    print(f"📊 Текущий webhook URL: {webhook_info.url}")
    print(f"📊 Необработанных обновлений: {webhook_info.pending_update_count}")
    
    print("\n🚀 ВАРИАНТЫ АВТОМАТИЧЕСКОЙ НАСТРОЙКИ:")
    print("=" * 50)
    
    print("1. 🌐 ОБЛАЧНЫЕ СЕРВИСЫ (рекомендуется):")
    print("   • Heroku: Бесплатный хостинг с HTTPS")
    print("   • Railway: Простая настройка")
    print("   • Render: Бесплатный план")
    print("   • Vercel: Для Python приложений")
    
    print("\n2. 🏠 ЛОКАЛЬНАЯ РАЗРАБОТКА:")
    print("   • ngrok: Туннель для локального сервера")
    print("   • localtunnel: Альтернатива ngrok")
    print("   • cloudflared: Туннель от Cloudflare")
    
    print("\n3. 🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА:")
    print("   • Скрипт для настройки webhook")
    print("   • Автоматическое получение URL")
    print("   • Проверка статуса webhook")

async def setup_auto_webhook():
    """Автоматическая настройка webhook"""
    
    print("\n🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА WEBHOOK")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return
    
    bot = Bot(token=bot_token)
    
    # Очищаем текущий webhook
    try:
        await bot.delete_webhook()
        print("✅ Старый webhook удален")
    except Exception as e:
        print(f"⚠️ Ошибка удаления webhook: {e}")
    
    # Очищаем необработанные обновления
    webhook_info = await bot.get_webhook_info()
    if webhook_info.pending_update_count > 0:
        print(f"🔄 Очищаем {webhook_info.pending_update_count} необработанных обновлений...")
        try:
            updates = await bot.get_updates(limit=1000, timeout=30)
            print(f"✅ Очищено {len(updates)} обновлений")
        except Exception as e:
            print(f"❌ Ошибка очистки: {e}")
    
    print("\n📋 ИНСТРУКЦИИ ДЛЯ АВТОМАТИЧЕСКОЙ НАСТРОЙКИ:")
    print("=" * 50)
    
    print("1. 🌐 HEROKU (рекомендуется):")
    print("   • Создайте аккаунт на heroku.com")
    print("   • Установите Heroku CLI")
    print("   • Создайте приложение: heroku create your-app-name")
    print("   • Деплойте код: git push heroku main")
    print("   • Настройте webhook: heroku run python setup_webhook.py")
    
    print("\n2. 🏠 NGROK (для тестирования):")
    print("   • Скачайте ngrok: https://ngrok.com/")
    print("   • Запустите: ngrok http 8080")
    print("   • Скопируйте HTTPS URL")
    print("   • Запустите: python setup_webhook.py")
    
    print("\n3. 🔧 АВТОМАТИЧЕСКИЙ СКРИПТ:")
    print("   • Создайте webhook сервер")
    print("   • Настройте автоматическое получение URL")
    print("   • Зарегистрируйте webhook")

if __name__ == "__main__":
    asyncio.run(explain_webhook())
    asyncio.run(setup_auto_webhook())
