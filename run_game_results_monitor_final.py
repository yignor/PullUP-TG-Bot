#!/usr/bin/env python3
"""
Скрипт для запуска финальной системы мониторинга результатов игр
"""

import asyncio
from game_results_monitor_final import GameResultsMonitorFinal

async def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ФИНАЛЬНОЙ СИСТЕМЫ МОНИТОРИНГА РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    monitor = GameResultsMonitorFinal()
    await monitor.run_game_results_monitor()

if __name__ == "__main__":
    asyncio.run(main())
