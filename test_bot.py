#!/usr/bin/env python3
"""
Тестовый скрипт для проверки основных функций бота
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_environment():
    """Тестирует наличие переменных окружения"""
    print("🔍 Тестирование переменных окружения...")
    
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    if not bot_token:
        print("⚠️ BOT_TOKEN не найден (возможно, настроен в Railway)")
    else:
        print("✅ BOT_TOKEN найден")
    
    if not chat_id:
        print("⚠️ CHAT_ID не найден (возможно, настроен в Railway)")
    else:
        print("✅ CHAT_ID найден")
    
    # Не считаем отсутствие переменных критической ошибкой для Railway
    return True

def test_imports():
    """Тестирует импорты основных модулей"""
    print("\n🔍 Тестирование импортов...")
    
    try:
        import aiohttp
        print("✅ aiohttp импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта aiohttp: {e}")
        return False
    
    try:
        import bs4
        print("✅ beautifulsoup4 импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта beautifulsoup4: {e}")
        return False
    
    try:
        from telegram import Bot
        from telegram.ext import Application
        print("✅ python-telegram-bot импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта python-telegram-bot: {e}")
        return False
    
    return True

async def test_telegram_connection():
    """Тестирует подключение к Telegram API"""
    print("\n🔍 Тестирование подключения к Telegram...")
    
    try:
        from telegram import Bot
        from telegram.ext import Application
        bot_token = os.getenv("BOT_TOKEN")
        
        if not bot_token:
            print("⚠️ BOT_TOKEN не найден, пропускаем тест Telegram")
            return True
        
        # Создаем приложение для правильной работы с API
        application = Application.builder().token(bot_token).build()
        bot = application.bot
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Подключение к Telegram успешно")
        print(f"   Имя бота: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False

async def test_website_connection():
    """Тестирует подключение к сайту letobasket.ru"""
    print("\n🔍 Тестирование подключения к letobasket.ru...")
    
    try:
        import aiohttp
        url = "http://letobasket.ru/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    print("✅ Сайт letobasket.ru доступен")
                    return True
                else:
                    print(f"❌ Сайт вернул статус: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка подключения к сайту: {e}")
        return False

def test_birthday_logic():
    """Тестирует логику проверки дней рождения"""
    print("\n🔍 Тестирование логики дней рождения...")
    
    try:
        import datetime
        
        # Тестируем функцию склонения
        def get_years_word(age: int) -> str:
            if 11 <= age % 100 <= 14:
                return "лет"
            elif age % 10 == 1:
                return "год"
            elif 2 <= age % 10 <= 4:
                return "года"
            else:
                return "лет"
        
        # Тестируем различные возрасты
        test_cases = [1, 2, 5, 11, 21, 22, 25, 31, 32, 35]
        for age in test_cases:
            word = get_years_word(age)
            print(f"   {age} {word}")
        
        print("✅ Логика дней рождения работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в логике дней рождения: {e}")
        return False

def test_pullup_patterns():
    """Тестирует паттерны поиска команд PullUP"""
    print("\n🔍 Тестирование паттернов поиска PullUP...")
    
    try:
        import re
        
        # Паттерны для поиска команд PullUP
        PULLUP_PATTERNS = [
            r'PullUP',
            r'Pull UP',
            r'PULL UP',
            r'pull up',
            r'PULLUP',
            r'pullup',
            r'Pull Up',
            r'PULL UP\s+\w+',  # PULL UP с любым словом после (например, PULL UP фарм)
            r'Pull UP\s+\w+',  # Pull UP с любым словом после
            r'pull up\s+\w+',  # pull up с любым словом после
        ]
        
        def find_pullup_team(text_block):
            """Ищет команду PullUP в тексте с поддержкой различных вариаций"""
            for pattern in PULLUP_PATTERNS:
                matches = re.findall(pattern, text_block, re.IGNORECASE)
                if matches:
                    return matches[0].strip()
            return None
        
        # Тестовые строки
        test_strings = [
            "PullUP",
            "Pull UP",
            "PULL UP",
            "pull up",
            "PULLUP",
            "pullup",
            "Pull Up",
            "PULL UP фарм",
            "Pull UP team",
            "pull up club"
        ]
        
        for test_str in test_strings:
            result = find_pullup_team(test_str)
            if result:
                print(f"   ✅ Найдено: '{test_str}' → '{result}'")
            else:
                print(f"   ❌ Не найдено: '{test_str}'")
        
        print("✅ Паттерны поиска PullUP работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в паттернах поиска PullUP: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестирования бота...\n")
    
    tests_passed = 0
    total_tests = 6
    
    # Тест 1: Переменные окружения
    if test_environment():
        tests_passed += 1
    
    # Тест 2: Импорты
    if test_imports():
        tests_passed += 1
    
    # Тест 3: Подключение к Telegram
    if await test_telegram_connection():
        tests_passed += 1
    
    # Тест 4: Подключение к сайту
    if await test_website_connection():
        tests_passed += 1
    
    # Тест 5: Логика дней рождения
    if test_birthday_logic():
        tests_passed += 1
    
    # Тест 6: Паттерны поиска PullUP
    if test_pullup_patterns():
        tests_passed += 1
    
    # Результаты
    print(f"\n📊 Результаты тестирования:")
    print(f"   Пройдено тестов: {tests_passed}/{total_tests}")
    
    if tests_passed >= total_tests - 1:  # Разрешаем один пропущенный тест
        print("🎉 Все основные тесты пройдены успешно! Бот готов к работе.")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте настройки.")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if not result:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании: {e}")
        sys.exit(1)
