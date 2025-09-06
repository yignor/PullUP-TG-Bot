#!/usr/bin/env python3
"""
Скрипт для запуска финальной системы мониторинга результатов игр
"""

import asyncio
import sys
from game_results_monitor_final import GameResultsMonitorFinal

async def main():
    """Основная функция"""
    # Проверяем, есть ли аргумент для принудительного запуска
    force_run = "--force" in sys.argv or "-f" in sys.argv
    
    if force_run:
        print("🚀 ЗАПУСК ФИНАЛЬНОЙ СИСТЕМЫ МОНИТОРИНГА РЕЗУЛЬТАТОВ (ПРИНУДИТЕЛЬНО)")
    else:
        print("🚀 ЗАПУСК ФИНАЛЬНОЙ СИСТЕМЫ МОНИТОРИНГА РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    monitor = GameResultsMonitorFinal()
    await monitor.run_game_results_monitor(force_run=force_run)

if __name__ == "__main__":
    asyncio.run(main())
