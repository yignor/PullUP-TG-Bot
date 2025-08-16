#!/usr/bin/env python3
"""
Скрипт для проверки текущих настроек окружения
"""

import os
from dotenv import load_dotenv

def check_current_settings():
    """Проверяет текущие настройки окружения"""
    print("🔍 ПРОВЕРКА ТЕКУЩИХ НАСТРОЕК ОКРУЖЕНИЯ\n")
    
    # Загружаем переменные окружения
    try:
        load_dotenv()
        print("✅ Переменные окружения загружены")
    except Exception as e:
        print(f"❌ Ошибка загрузки переменных: {e}")
        return
    
    # Проверяем основные настройки
    print("\n📋 Основные настройки:")
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if bot_token:
        print(f"   ✅ BOT_TOKEN: {bot_token[:10]}...")
    else:
        print("   ❌ BOT_TOKEN: не установлен")
    
    if chat_id:
        print(f"   ✅ CHAT_ID: {chat_id}")
    else:
        print("   ❌ CHAT_ID: не установлен")
    
    # Проверяем тестовые настройки
    print("\n🧪 Тестовые настройки:")
    
    test_bot_token = os.getenv('TEST_BOT_TOKEN')
    test_chat_id = os.getenv('TEST_CHAT_ID')
    
    if test_bot_token:
        print(f"   ✅ TEST_BOT_TOKEN: {test_bot_token[:10]}...")
    else:
        print("   ❌ TEST_BOT_TOKEN: не установлен")
    
    if test_chat_id:
        print(f"   ✅ TEST_CHAT_ID: {test_chat_id}")
    else:
        print("   ❌ TEST_CHAT_ID: не установлен")
    
    # Определяем текущий режим
    print("\n🎯 Текущий режим:")
    
    if bot_token and chat_id:
        if chat_id == "-1001535261616":
            print("   🏭 ПРОДАКШН режим (основной чат)")
        elif chat_id == "-15573582":
            print("   🧪 ТЕСТОВЫЙ режим (тестовый чат)")
        else:
            print(f"   ⚠️ НЕИЗВЕСТНЫЙ режим (CHAT_ID: {chat_id})")
    else:
        print("   ❌ НАСТРОЙКИ НЕ УСТАНОВЛЕНЫ")
    
    # Проверяем дополнительные настройки
    print("\n🔧 Дополнительные настройки:")
    
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    if spreadsheet_id:
        print(f"   ✅ SPREADSHEET_ID: {spreadsheet_id}")
    else:
        print("   ❌ SPREADSHEET_ID: не установлен")
    
    announcements_topic_id = os.getenv('ANNOUNCEMENTS_TOPIC_ID')
    if announcements_topic_id and announcements_topic_id != "your_topic_id_here":
        print(f"   ✅ ANNOUNCEMENTS_TOPIC_ID: {announcements_topic_id}")
    else:
        print("   ⚠️ ANNOUNCEMENTS_TOPIC_ID: не настроен")
    
    # Рекомендации
    print("\n💡 Рекомендации:")
    
    if not bot_token or not chat_id:
        print("   ❌ Установите основные настройки BOT_TOKEN и CHAT_ID")
    
    if not test_bot_token or not test_chat_id:
        print("   ⚠️ Рекомендуется установить тестовые настройки TEST_BOT_TOKEN и TEST_CHAT_ID")
    
    if chat_id == "-1001535261616":
        print("   ✅ Продакшн режим активен - можно запускать основные скрипты")
        print("   💡 Для тестирования используйте: python test_with_test_settings.py")
    
    elif chat_id == "-15573582":
        print("   ✅ Тестовый режим активен - можно тестировать функционал")
        print("   💡 Для продакшна измените CHAT_ID на -1001535261616")
    
    print("\n📝 Для изменения настроек отредактируйте файл .env вручную")
    print("📖 Подробные инструкции: ENVIRONMENT_SETUP.md")

if __name__ == "__main__":
    check_current_settings()
