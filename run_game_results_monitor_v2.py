#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга результатов игр (версия 2) в GitHub Actions
Прямое сканирование табло без зависимости от GameSystemManager
"""

import asyncio
from game_results_monitor_v2 import run_game_results_monitor_v2

async def main():
    """Основная функция для запуска мониторинга результатов игр"""
    print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР (ВЕРСИЯ 2)")
    print("=" * 60)
    
    # Используем централизованное логирование времени
    from datetime_utils import get_moscow_time
    now = get_moscow_time()
    print(f"🕐 Текущее время (Москва): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"🔄 Workflow запущен: {now.strftime('%H:%M:%S')}")
    
    # Показываем информацию о расписании
    weekday = now.weekday()  # 0=Пн, 1=Вт, ..., 6=Вс
    hour = now.hour
    
    # Определяем день недели
    if weekday < 5:  # Пн-Пт (0-4)
        day_type = "будни"
        if 18 <= hour <= 23 or hour == 0:
            print(f"📅 Режим: {day_type} (запуск каждые 15 минут, 18:00-01:00)")
        else:
            print(f"📅 Режим: {day_type} (неактивное время)")
    else:  # Сб-Вс (5-6)
        day_type = "выходные"
        if 11 <= hour <= 23 or hour == 0:
            print(f"📅 Режим: {day_type} (запуск каждые 15 минут, 11:00-01:00)")
        else:
            print(f"📅 Режим: {day_type} (неактивное время)")
    
    try:
        # Запускаем мониторинг
        await run_game_results_monitor_v2()
        
        print("=" * 60)
        print("✅ Мониторинг результатов завершен")
        
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
