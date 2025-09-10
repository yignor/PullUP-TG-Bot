#!/usr/bin/env python3
"""
Автоматическая настройка webhook с использованием ngrok
"""

import asyncio
import os
import subprocess
import time
import requests
from dotenv import load_dotenv
from telegram import Bot

async def setup_auto_webhook():
    """Автоматическая настройка webhook"""
    
    print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА WEBHOOK")
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
    
    print("\n🔧 ВАРИАНТЫ АВТОМАТИЧЕСКОЙ НАСТРОЙКИ:")
    print("=" * 50)
    
    print("1. 🌐 NGROK (рекомендуется для тестирования):")
    print("   • Автоматически создает HTTPS туннель")
    print("   • Не требует настройки сервера")
    print("   • Идеально для разработки и тестирования")
    
    print("\n2. ☁️ ОБЛАЧНЫЕ СЕРВИСЫ:")
    print("   • Heroku: heroku create your-app-name")
    print("   • Railway: railway deploy")
    print("   • Render: render.com")
    
    print("\n3. 🏠 ЛОКАЛЬНЫЙ СЕРВЕР:")
    print("   • Требует настройки HTTPS")
    print("   • Подходит для продакшена")
    
    # Проверяем наличие ngrok
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n✅ NGROK найден: {result.stdout.strip()}")
            await setup_ngrok_webhook(bot)
        else:
            print("\n❌ NGROK не найден")
            print_ngrok_instructions()
    except FileNotFoundError:
        print("\n❌ NGROK не установлен")
        print_ngrok_instructions()

async def setup_ngrok_webhook(bot):
    """Настройка webhook через ngrok"""
    
    print("\n🔧 НАСТРОЙКА WEBHOOK ЧЕРЕЗ NGROK")
    print("=" * 50)
    
    # Запускаем ngrok
    print("🚀 Запускаем ngrok...")
    ngrok_process = subprocess.Popen(['ngrok', 'http', '8080'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    
    # Ждем запуска ngrok
    time.sleep(3)
    
    try:
        # Получаем URL от ngrok
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            if tunnels:
                ngrok_url = tunnels[0]['public_url']
                webhook_url = f"{ngrok_url}/webhook"
                
                print(f"✅ NGROK URL: {ngrok_url}")
                print(f"✅ Webhook URL: {webhook_url}")
                
                # Настраиваем webhook
                await bot.set_webhook(url=webhook_url)
                print("✅ Webhook настроен успешно")
                
                # Проверяем webhook
                webhook_info = await bot.get_webhook_info()
                print(f"📊 Webhook URL: {webhook_info.url}")
                print(f"📊 Pending updates: {webhook_info.pending_update_count}")
                
                print("\n🎉 WEBHOOK НАСТРОЕН УСПЕШНО!")
                print("=" * 50)
                print("Теперь все обновления будут приходить на ваш сервер")
                print("Запустите webhook сервер:")
                print("   python webhook_server.py --port 8080")
                
                return webhook_url
            else:
                print("❌ NGROK туннели не найдены")
        else:
            print("❌ Ошибка получения URL от ngrok")
    
    except Exception as e:
        print(f"❌ Ошибка настройки ngrok: {e}")
    
    finally:
        # Останавливаем ngrok
        ngrok_process.terminate()

def print_ngrok_instructions():
    """Инструкции по установке ngrok"""
    
    print("\n📋 ИНСТРУКЦИИ ПО УСТАНОВКЕ NGROK:")
    print("=" * 50)
    
    print("1. 🌐 Скачайте ngrok:")
    print("   • Перейдите на https://ngrok.com/")
    print("   • Зарегистрируйтесь (бесплатно)")
    print("   • Скачайте ngrok для вашей ОС")
    
    print("\n2. 🔧 Установите ngrok:")
    print("   • macOS: brew install ngrok/ngrok/ngrok")
    print("   • Linux: sudo apt install ngrok")
    print("   • Windows: скачайте .exe файл")
    
    print("\n3. 🔑 Настройте токен:")
    print("   • Получите токен на https://dashboard.ngrok.com/get-started/your-authtoken")
    print("   • Выполните: ngrok config add-authtoken YOUR_TOKEN")
    
    print("\n4. 🚀 Запустите ngrok:")
    print("   • ngrok http 8080")
    print("   • Скопируйте HTTPS URL")
    print("   • Запустите этот скрипт снова")

if __name__ == "__main__":
    asyncio.run(setup_auto_webhook())
