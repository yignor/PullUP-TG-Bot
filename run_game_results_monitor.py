#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга результатов игр в GitHub Actions
"""

import asyncio
import json
import os
from game_results_monitor import GameResultsMonitor, load_game_monitor_history
from datetime_utils import get_moscow_time

async def run_game_results_monitor():
    """Запускает мониторинг результатов игр"""
    print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
    print("=" * 60)
    
    # Используем централизованное логирование времени
    now = get_moscow_time()
    print(f"🕐 Текущее время (Москва): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    
    try:
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        print(f"📋 История мониторинга содержит {len(monitor_history)} записей")
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        
        # Проверяем активные мониторинги
        active_monitors = 0
        completed_monitors = 0
        
        for game_key, monitor_info in monitor_history.items():
            status = monitor_info.get('status', 'unknown')
            
            if status == 'monitoring':
                active_monitors += 1
                game_info = monitor_info.get('game_info', {})
                game_link = monitor_info.get('game_link', '')
                
                print(f"\n🎮 Проверяем активный мониторинг: {game_key}")
                print(f"   Дата: {game_info.get('date', 'N/A')}")
                print(f"   Время: {game_info.get('time', 'N/A')}")
                print(f"   Команды: {game_info.get('team1', 'N/A')} vs {game_info.get('team2', 'N/A')}")
                
                # Проверяем состояние игры
                scoreboard_info = await monitor.parse_game_scoreboard(game_link)
                
                if scoreboard_info:
                    print(f"   📊 Период: {scoreboard_info['period']}, Время: {scoreboard_info['timer']}")
                    print(f"   🏀 Счет: {scoreboard_info['score1']} : {scoreboard_info['score2']}")
                    
                    if scoreboard_info['is_game_finished']:
                        print(f"   🏁 Игра завершена! Отправляем уведомление")
                        
                        # Отправляем уведомление
                        success = await monitor.send_game_result_notification(
                            game_info, scoreboard_info, game_link
                        )
                        
                        if success:
                            # Обновляем статус в истории
                            monitor_info['status'] = 'completed'
                            monitor_info['end_time'] = get_moscow_time().isoformat()
                            completed_monitors += 1
                            print(f"   ✅ Уведомление отправлено, мониторинг завершен")
                            
                            # Сохраняем историю и завершаем workflow
                            save_game_monitor_history(monitor_history)
                            print(f"   🏁 Workflow завершен после отправки уведомления")
                            return  # Завершаем выполнение
                        else:
                            print(f"   ❌ Ошибка отправки уведомления")
                    else:
                        print(f"   ⏳ Игра еще идет, продолжаем мониторинг")
                else:
                    print(f"   ⚠️ Не удалось получить данные табло")
            
            elif status == 'completed':
                completed_monitors += 1
        
        # Сохраняем обновленную историю
        from game_results_monitor import save_game_monitor_history
        save_game_monitor_history(monitor_history)
        
        print(f"\n📋 ИТОГИ МОНИТОРИНГА:")
        print(f"   Активных мониторингов: {active_monitors}")
        print(f"   Завершенных мониторингов: {completed_monitors}")
        print(f"   Всего записей в истории: {len(monitor_history)}")
        
        if active_monitors == 0:
            print(f"   ℹ️ Нет активных мониторингов")
        
        print(f"\n✅ Мониторинг результатов завершен")
        
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_game_results_monitor())
