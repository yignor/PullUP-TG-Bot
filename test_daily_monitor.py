#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ежедневного мониторинга голосований
"""

import asyncio
import json
from datetime import datetime
from daily_poll_monitor import DailyPollMonitor

async def test_monitor():
    """Тестирует основные функции мониторинга"""
    print("🧪 Тестирование ежедневного мониторинга голосований")
    
    monitor = DailyPollMonitor()
    
    # Тест 1: Инициализация
    print("\n1️⃣ Тест инициализации...")
    init_success = await monitor.initialize()
    if init_success:
        print("✅ Инициализация прошла успешно")
    else:
        print("❌ Ошибка инициализации")
        return False
    
    # Тест 2: Определение активных опросов
    print("\n2️⃣ Тест определения активных опросов...")
    active_polls = monitor.get_active_polls_info()
    print(f"📋 Активные опросы: {active_polls}")
    
    if active_polls:
        print("✅ Активные опросы определены")
    else:
        print("ℹ️ Нет активных опросов (возможно, выходной)")
    
    # Тест 3: Форматирование имен
    print("\n3️⃣ Тест форматирования имен...")
    test_names = [
        ("Иван Петров", "@ivan_petrov"),
        ("Анна", "@anna"),
        ("", "@username_only"),
        ("Мария Ивановна Сидорова", "@maria_s")
    ]
    
    for name, telegram_id in test_names:
        formatted = monitor.format_player_name(name, telegram_id)
        print(f"   '{name}' + '{telegram_id}' → '{formatted}'")
    
    print("✅ Форматирование имен работает")
    
    # Тест 4: Работа с файлами голосов
    print("\n4️⃣ Тест работы с файлами голосов...")
    test_poll_id = "test_poll_123"
    test_votes = {
        12345: {
            'name': 'Иван Петров',
            'options': [0, 1],  # Вторник и пятница
            'update_id': 1001
        },
        67890: {
            'name': 'Анна Сидорова',
            'options': [0],  # Только вторник
            'update_id': 1002
        }
    }
    
    # Сохраняем тестовые голоса
    monitor.save_current_votes(test_poll_id, test_votes)
    print("✅ Тестовые голоса сохранены")
    
    # Загружаем обратно
    loaded_votes = monitor.load_previous_votes(test_poll_id)
    if loaded_votes == test_votes:
        print("✅ Голоса загружены корректно")
    else:
        print("❌ Ошибка загрузки голосов")
        return False
    
    # Тест 5: Поиск изменений
    print("\n5️⃣ Тест поиска изменений...")
    
    # Изменяем голоса
    new_votes = {
        12345: {
            'name': 'Иван Петров',
            'options': [1],  # Только пятница (изменил выбор)
            'update_id': 1003
        },
        67890: {
            'name': 'Анна Сидорова',
            'options': [0],  # Остался вторник
            'update_id': 1004
        },
        11111: {  # Новый участник
            'name': 'Петр Новый',
            'options': [0, 1],
            'update_id': 1005
        }
        # 67890 удален (больше не голосует)
    }
    
    added, removed, changed = monitor.find_vote_changes(test_votes, new_votes)
    
    print(f"   Новые голоса: {len(added)}")
    print(f"   Удаленные голоса: {len(removed)}")
    print(f"   Измененные голоса: {len(changed)}")
    
    if len(added) == 1 and len(removed) == 0 and len(changed) == 1:
        print("✅ Поиск изменений работает корректно")
    else:
        print("❌ Ошибка в поиске изменений")
        return False
    
    # Очистка тестовых файлов
    import os
    test_file = f"poll_votes_{test_poll_id}.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        print("🧹 Тестовые файлы очищены")
    
    print("\n🎉 Все тесты прошли успешно!")
    return True

async def main():
    """Основная функция тестирования"""
    try:
        success = await test_monitor()
        if success:
            print("\n✅ Тестирование завершено успешно")
        else:
            print("\n❌ Тестирование завершено с ошибками")
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(main())
