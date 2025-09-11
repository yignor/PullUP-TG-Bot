#!/usr/bin/env python3
"""
Скрипт для запуска ежедневного мониторинга голосований за тренировки
"""

import asyncio
import sys
import os
from datetime_utils import log_current_time
from daily_poll_monitor import DailyPollMonitor

async def main():
    """Основная функция запуска мониторинга"""
    print("🚀 Запуск ежедневного мониторинга голосований за тренировки")
    log_current_time()
    
    try:
        monitor = DailyPollMonitor()
        success = await monitor.run_daily_check()
        
        if success:
            print("✅ Мониторинг завершен успешно")
            sys.exit(0)
        else:
            print("❌ Мониторинг завершен с ошибками")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
