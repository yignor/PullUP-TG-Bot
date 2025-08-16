#!/usr/bin/env python3
"""
Скрипт для тестирования функционала дней рождения
"""

import datetime
import os
from dotenv import load_dotenv
from birthday_bot_simple import players, get_years_word, should_check_birthdays

def load_env_variables():
    """Загружает переменные из .env файла"""
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Переменные загружены из .env файла")
        except FileNotFoundError:
            print("❌ Файл .env не найден")
            return False
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True

def test_birthday_functionality():
    """Тестирует функционал дней рождения"""
    print("\n=== ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА ДНЕЙ РОЖДЕНИЯ ===\n")
    
    if not load_env_variables():
        return
    
    # Проверяем текущее время
    now = datetime.datetime.now()
    print(f"1. Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем, нужно ли проверять дни рождения
    should_check = should_check_birthdays()
    print(f"2. Нужно ли проверять дни рождения: {'✅ Да' if should_check else '❌ Нет'}")
    
    # Проверяем дни рождения на сегодня
    print(f"\n3. Проверка дней рождения на {now.strftime('%Y-%m-%d')}:")
    today_md = now.strftime("%m-%d")
    birthday_people = []
    
    for player in players:
        try:
            birthday = datetime.datetime.strptime(player["birthday"], "%Y-%m-%d")
            if birthday.strftime("%m-%d") == today_md:
                age = now.year - birthday.year
                birthday_people.append(f"{player['name']} ({age} {get_years_word(age)})")
                print(f"   ✅ {player['name']} - {age} {get_years_word(age)}")
        except Exception as e:
            print(f"   ❌ Ошибка при обработке {player['name']}: {e}")
    
    if birthday_people:
        print(f"\n4. Именинники сегодня: {', '.join(birthday_people)}")
        message = "🎉 Сегодня день рождения у " + ", ".join(birthday_people) + "! \n Поздравляем! 🎂"
        print(f"5. Сообщение для отправки: {message}")
    else:
        print("4. Сегодня нет именинников")
    
    # Проверяем ближайшие дни рождения
    print(f"\n6. Ближайшие дни рождения:")
    upcoming_birthdays = []
    
    for i in range(1, 31):  # Проверяем следующие 30 дней
        future_date = now + datetime.timedelta(days=i)
        future_md = future_date.strftime("%m-%d")
        
        for player in players:
            try:
                birthday = datetime.datetime.strptime(player["birthday"], "%Y-%m-%d")
                if birthday.strftime("%m-%d") == future_md:
                    age = future_date.year - birthday.year
                    upcoming_birthdays.append({
                        'name': player['name'],
                        'date': future_date.strftime('%Y-%m-%d'),
                        'age': age,
                        'days_until': i
                    })
            except Exception:
                continue
    
    # Сортируем по количеству дней до дня рождения
    upcoming_birthdays.sort(key=lambda x: x['days_until'])
    
    for i, birthday in enumerate(upcoming_birthdays[:5], 1):  # Показываем первые 5
        print(f"   {i}. {birthday['name']} - {birthday['date']} ({birthday['age']} {get_years_word(birthday['age'])}) - через {birthday['days_until']} дней")
    
    # Проверяем функционал опросов
    print(f"\n7. Проверка функционала опросов:")
    if should_check and birthday_people:
        print("   ✅ Можно создать опрос для поздравления")
    else:
        print("   ⚠️ Не время для создания опросов или нет именинников")
    
    # Проверяем файлы ботов
    print(f"\n8. Проверка файлов ботов:")
    import os
    
    bot_files = [
        'birthday_bot.py',
        'birthday_bot_simple.py',
        'pullup_notifications.py'
    ]
    
    for bot_file in bot_files:
        if os.path.exists(bot_file):
            print(f"   ✅ {bot_file} - существует")
        else:
            print(f"   ❌ {bot_file} - не найден")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    test_birthday_functionality()
