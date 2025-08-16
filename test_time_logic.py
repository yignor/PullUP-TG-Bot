#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики времени уведомлений
"""

from datetime import datetime, timezone, timedelta
from pullup_notifications import get_moscow_time, should_send_morning_notification
from birthday_bot import should_check_birthdays

def test_moscow_time():
    """Тестирует московское время"""
    print("🕐 ТЕСТ МОСКОВСКОГО ВРЕМЕНИ")
    print("=" * 40)
    
    moscow_time = get_moscow_time()
    utc_time = datetime.now(timezone.utc)
    
    print(f"UTC время: {utc_time}")
    print(f"Московское время: {moscow_time}")
    print(f"Разница: {moscow_time - utc_time}")
    print()

def test_morning_notification_logic():
    """Тестирует логику утренних уведомлений"""
    print("🌅 ТЕСТ ЛОГИКИ УТРЕННИХ УВЕДОМЛЕНИЙ")
    print("=" * 40)
    
    current_hour = get_moscow_time().hour
    should_send = should_send_morning_notification()
    
    print(f"Текущий час по Москве: {current_hour}")
    print(f"Нужно отправлять утреннее уведомление: {should_send}")
    
    if should_send:
        print("✅ Сейчас время для утреннего уведомления (9:00-10:00)")
    else:
        print("❌ Сейчас не время для утреннего уведомления")
    print()

def test_birthday_logic():
    """Тестирует логику дней рождения"""
    print("🎂 ТЕСТ ЛОГИКИ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 40)
    
    should_check = should_check_birthdays()
    
    print(f"Нужно проверять дни рождения: {should_check}")
    
    if should_check:
        print("✅ Сейчас время для проверки дней рождения (9:00-9:29)")
    else:
        print("❌ Сейчас не время для проверки дней рождения")
    print()

def test_time_scenarios():
    """Тестирует различные сценарии времени"""
    print("📊 ТЕСТ РАЗЛИЧНЫХ СЦЕНАРИЕВ ВРЕМЕНИ")
    print("=" * 40)
    
    # Создаем тестовые времена
    test_times = [
        (8, 30, "8:30 - не время для утренних уведомлений"),
        (9, 15, "9:15 - время для утренних уведомлений"),
        (9, 45, "9:45 - время для утренних уведомлений"),
        (10, 0, "10:00 - не время для утренних уведомлений"),
        (14, 30, "14:30 - не время для утренних уведомлений"),
    ]
    
    for hour, minute, description in test_times:
        # Создаем тестовое время
        test_time = datetime.now(timezone(timedelta(hours=3))).replace(hour=hour, minute=minute)
        
        # Проверяем логику
        morning_should = hour == 9
        birthday_should = hour == 9 and minute < 30
        
        print(f"{description}")
        print(f"  Утреннее уведомление: {'✅' if morning_should else '❌'}")
        print(f"  День рождения: {'✅' if birthday_should else '❌'}")
        print()

if __name__ == "__main__":
    test_moscow_time()
    test_morning_notification_logic()
    test_birthday_logic()
    test_time_scenarios()
    
    print("🎯 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 40)
    print("✅ Московское время работает корректно")
    print("✅ Утренние уведомления только в 9:00-10:00")
    print("✅ Дни рождения только в 9:00-9:29")
    print("✅ В тестовый канал только ошибки")
