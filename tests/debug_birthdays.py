#!/usr/bin/env python3
"""
Тестовый скрипт для проверки дней рождения
"""
import sys
import os
sys.path.append('..')

import datetime
from birthday_bot import players, should_check_birthdays, get_years_word

def debug_birthdays():
    """Отладочная функция для дней рождения"""
    print("🎂 ОТЛАДКА ДНЕЙ РОЖДЕНИЯ")
    print("=" * 50)
    
    # Текущее время
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    print(f"Текущее московское время: {now.strftime('%H:%M:%S')}")
    
    # Проверяем логику времени
    should_check = should_check_birthdays()
    print(f"Должно проверять дни рождения: {'✅ ДА' if should_check else '❌ НЕТ'}")
    
    # Проверяем сегодняшнюю дату
    today = datetime.datetime.now()
    today_md = today.strftime("%m-%d")
    print(f"Сегодняшняя дата (MM-DD): {today_md}")
    
    # Ищем дни рождения
    birthday_people = []
    print("\n📅 Проверка дней рождения:")
    
    for p in players:
        try:
            bd = datetime.datetime.strptime(p["birthday"], "%Y-%m-%d")
            bd_md = bd.strftime("%m-%d")
            
            if bd_md == today_md:
                age = today.year - bd.year
                birthday_people.append(f"{p['name']} ({age} {get_years_word(age)})")
                print(f"  🎉 {p['name']} - {p['birthday']} ({age} {get_years_word(age)})")
            else:
                print(f"  📅 {p['name']} - {p['birthday']} (не сегодня)")
        except Exception as e:
            print(f"  ❌ Ошибка с {p['name']}: {e}")
    
    print(f"\n🎂 ИТОГО ДНЕЙ РОЖДЕНИЯ СЕГОДНЯ: {len(birthday_people)}")
    
    if birthday_people:
        print("Люди с днями рождения:")
        for person in birthday_people:
            print(f"  - {person}")
    else:
        print("Сегодня нет дней рождения")
    
    print("\n" + "=" * 50)
    print("✅ ОТЛАДКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    debug_birthdays()
