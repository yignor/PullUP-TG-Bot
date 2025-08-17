#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики времени
Помогает понять, когда отправляются уведомления
"""
import sys
import os
sys.path.append('..')

import datetime
from datetime import time
from pullup_notifications import should_send_morning_notification, get_moscow_time

def test_time_logic():
    """Тестирует логику времени"""
    print("🕐 ТЕСТИРОВАНИЕ ЛОГИКИ ВРЕМЕНИ")
    print("=" * 50)
    
    # Текущее время
    moscow_time = get_moscow_time()
    print(f"Текущее московское время: {moscow_time.strftime('%H:%M:%S')}")
    
    # Проверяем логику утренних уведомлений
    should_send = should_send_morning_notification()
    print(f"Должно отправляться утреннее уведомление: {'✅ ДА' if should_send else '❌ НЕТ'}")
    
    # Тестируем разные времена
    print("\n📊 ТЕСТИРОВАНИЕ РАЗНЫХ ВРЕМЕН:")
    test_times = [
        (8, 59),  # 8:59 - не должно отправляться
        (9, 0),   # 9:00 - должно отправляться
        (9, 15),  # 9:15 - должно отправляться
        (9, 29),  # 9:29 - должно отправляться
        (9, 30),  # 9:30 - не должно отправляться
        (10, 0),  # 10:00 - не должно отправляться
    ]
    
    for hour, minute in test_times:
        # Создаем тестовое время
        test_time = moscow_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Проверяем логику
        should_send_test = (test_time.hour == 9 and test_time.minute < 30)
        
        print(f"  {hour:02d}:{minute:02d} - {'✅ ДА' if should_send_test else '❌ НЕТ'}")
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    test_time_logic()
