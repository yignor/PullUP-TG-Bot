#!/usr/bin/env python3
"""
Тестовый скрипт для GitHub Actions
Проверяет новую систему дней рождения
"""

import os
import asyncio
from players_manager import PlayersManager
from birthday_notifications import get_years_word, test_birthday_notifications

def test_google_sheets_connection():
    """Тестирует подключение к Google Sheets"""
    print("🧪 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К GOOGLE SHEETS")
    print("=" * 50)
    
    try:
        pm = PlayersManager()
        players = pm.get_all_players()
        print(f"✅ Подключение успешно! Загружено {len(players)} игроков")
        
        # Показываем несколько примеров
        for i, player in enumerate(players[:3], 1):
            surname = player.get('surname', '')
            name = player.get('name', '')
            nickname = player.get('nickname', '')
            telegram_id = player.get('telegram_id', '')
            print(f"{i}. {surname} {name} | Ник: \"{nickname}\" | Telegram: {telegram_id}")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_message_formatting():
    """Тестирует форматирование сообщений"""
    print("\n🧪 ТЕСТИРОВАНИЕ ФОРМАТИРОВАНИЯ СООБЩЕНИЙ")
    print("=" * 50)
    
    try:
        pm = PlayersManager()
        players = pm.get_all_players()
        
        print("📝 ПРИМЕРЫ ФОРМАТИРОВАНИЯ СООБЩЕНИЙ:")
        print("-" * 40)
        
        # Находим игрока с полными данными для примера
        example_player = None
        for player in players:
            if player.get('nickname') and player.get('telegram_id'):
                example_player = player
                break
        
        if example_player:
            surname = example_player.get('surname', '')
            nickname = example_player.get('nickname', '')
            telegram_id = example_player.get('telegram_id', '')
            first_name = example_player.get('name', '')
            age = example_player.get('age', 0)
            
            print("1. С никнеймом и Telegram ID:")
            print(f"🎉 Сегодня день рождения у {surname} \"{nickname}\" ({telegram_id}) {first_name} ({age} {get_years_word(age)})!")
            print(" Поздравляем! 🎂")
            print()
            
            print("2. Только с никнеймом:")
            print(f"🎉 Сегодня день рождения у {surname} \"{nickname}\" {first_name} ({age} {get_years_word(age)})!")
            print(" Поздравляем! 🎂")
            print()
            
            print("3. Только с Telegram ID:")
            print(f"🎉 Сегодня день рождения у {surname} ({telegram_id}) {first_name} ({age} {get_years_word(age)})!")
            print(" Поздравляем! 🎂")
            print()
            
            print("4. Без дополнительных данных:")
            print(f"🎉 Сегодня день рождения у {surname} {first_name} ({age} {get_years_word(age)})!")
            print(" Поздравляем! 🎂")
        else:
            print("⚠️ Не найден игрок с полными данными для примера")
        
        print("✅ Тест форматирования завершен")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования форматирования: {e}")
        return False

async def test_birthday_logic():
    """Тестирует логику дней рождения"""
    print("\n🧪 ТЕСТИРОВАНИЕ ЛОГИКИ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 50)
    
    try:
        await test_birthday_notifications()
        print("✅ Тест логики завершен успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования логики: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ НОВОЙ СИСТЕМЫ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 60)
    
    # Проверяем переменные окружения
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    print("🔧 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print(f"BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"GOOGLE_SHEETS_CREDENTIALS: {'✅' if google_credentials else '❌'}")
    print(f"SPREADSHEET_ID: {'✅' if spreadsheet_id else '❌'}")
    
    # Запускаем тесты
    tests_passed = 0
    total_tests = 3
    
    # Тест 1: Подключение к Google Sheets
    if test_google_sheets_connection():
        tests_passed += 1
    
    # Тест 2: Форматирование сообщений
    if test_message_formatting():
        tests_passed += 1
    
    # Тест 3: Логика дней рождения
    if await test_birthday_logic():
        tests_passed += 1
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎂 Новая система дней рождения готова к работе!")
        return True
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("🔧 Проверьте настройки и логи")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
