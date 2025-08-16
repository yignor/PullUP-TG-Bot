#!/usr/bin/env python3
"""
Тест новой логики сбора данных о посещаемости
"""

import datetime
from training_polls import get_target_training_day, should_collect_attendance

def test_attendance_logic():
    """Тестирует логику определения дня для сбора данных"""
    print("🏀 ТЕСТ ЛОГИКИ СБОРА ДАННЫХ О ПОСЕЩАЕМОСТИ")
    print("=" * 55)
    print()
    
    # Тестируем разные дни недели
    test_days = [
        (0, "Понедельник"),
        (1, "Вторник"), 
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье")
    ]
    
    print("📅 Тестирование функции get_target_training_day():")
    print("-" * 45)
    
    for weekday, day_name in test_days:
        # Создаем тестовую дату
        test_date = datetime.datetime.now().replace(weekday=weekday)
        target_day = get_target_training_day()
        
        if weekday == 2:  # Среда
            expected = "Вторник"
            status = "✅" if target_day == expected else "❌"
            print(f"{status} {day_name} -> Проверяем результаты за {target_day} (ожидалось: {expected})")
        elif weekday == 5:  # Суббота
            expected = "Пятница"
            status = "✅" if target_day == expected else "❌"
            print(f"{status} {day_name} -> Проверяем результаты за {target_day} (ожидалось: {expected})")
        else:
            status = "✅" if target_day is None else "❌"
            print(f"{status} {day_name} -> Не день сбора данных ({target_day})")
    
    print()
    print("🕐 Тестирование времени сбора данных:")
    print("-" * 35)
    
    # Тестируем разные часы
    test_hours = [8, 9, 10, 11]
    test_weekdays = [2, 5]  # Среда и суббота
    
    for weekday in test_weekdays:
        day_name = "Среда" if weekday == 2 else "Суббота"
        print(f"\n📅 {day_name}:")
        
        for hour in test_hours:
            # Создаем тестовую дату
            test_date = datetime.datetime.now().replace(weekday=weekday, hour=hour, minute=15)
            should_collect = should_collect_attendance()
            
            if hour == 9:
                status = "✅" if should_collect else "❌"
                print(f"   {status} {hour:02d}:15 -> Сбор данных: {should_collect} (ожидалось: True)")
            else:
                status = "✅" if not should_collect else "❌"
                print(f"   {status} {hour:02d}:15 -> Сбор данных: {should_collect} (ожидалось: False)")

def show_workflow():
    """Показывает рабочий процесс"""
    print("\n🔄 РАБОЧИЙ ПРОЦЕСС СБОРА ДАННЫХ")
    print("=" * 40)
    print()
    
    workflow = [
        {
            "day": "Воскресенье 9:00",
            "action": "Создается опрос на неделю",
            "description": "Bot создает опрос с вариантами: Вторник 19:00, Пятница 20:30, Тренер, Нет"
        },
        {
            "day": "Вторник 19:00",
            "action": "Проводится тренировка",
            "description": "Участники приходят на тренировку"
        },
        {
            "day": "Среда 9:00",
            "action": "Сбор данных за Вторник",
            "description": "Система проверяет результаты опроса за Вторник и сохраняет в Google Sheets"
        },
        {
            "day": "Пятница 20:30",
            "action": "Проводится тренировка",
            "description": "Участники приходят на тренировку"
        },
        {
            "day": "Суббота 9:00",
            "action": "Сбор данных за Пятницу",
            "description": "Система проверяет результаты опроса за Пятницу и сохраняет в Google Sheets"
        }
    ]
    
    for i, step in enumerate(workflow, 1):
        print(f"{i}. {step['day']}")
        print(f"   🎯 {step['action']}")
        print(f"   📝 {step['description']}")
        print()

def show_data_structure():
    """Показывает структуру данных"""
    print("📊 СТРУКТУРА СОХРАНЯЕМЫХ ДАННЫХ")
    print("=" * 35)
    print()
    
    print("🔑 Ключ в Google Sheets:")
    print("   Формат: YYYY-MM-DD_ДеньНедели")
    print("   Примеры:")
    print("   • 2024-01-15_Вторник")
    print("   • 2024-01-19_Пятница")
    print()
    
    print("📋 Данные:")
    print("   {")
    print('     "Вторник": ["Иван", "Петр", "Анна"]')
    print('     "Пятница": ["Мария", "Сергей"]')
    print('     "Тренер": ["Алексей"]')
    print('     "Нет": ["Дмитрий"]')
    print("   }")
    print()
    
    print("💡 Логика фильтрации:")
    print("   • Среда 9:00 -> Сохраняются только данные за Вторник")
    print("   • Суббота 9:00 -> Сохраняются только данные за Пятницу")

def main():
    """Основная функция"""
    test_attendance_logic()
    show_workflow()
    show_data_structure()
    
    print("🎯 ВЫВОД:")
    print("• Среда 9:00 -> Проверяем результаты за Вторник")
    print("• Суббота 9:00 -> Проверяем результаты за Пятницу")
    print("• Данные сохраняются с ключом YYYY-MM-DD_ДеньНедели")
    print("• Система автоматически фильтрует нужные данные")

if __name__ == "__main__":
    main()
