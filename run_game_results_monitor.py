#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга результатов игр в GitHub Actions
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from game_results_monitor import GameResultsMonitor, load_game_monitor_history, save_game_monitor_history
from datetime_utils import get_moscow_time, is_today
from game_system_manager import GameSystemManager

async def check_games_for_monitoring() -> list:
    """Проверяет игры, которые должны начаться в ближайшие 5 минут"""
    try:
        print("🔍 Проверяем игры для мониторинга...")
        
        # Создаем экземпляр GameSystemManager для парсинга расписания
        game_manager = GameSystemManager()
        
        # Парсим расписание
        schedule = await game_manager.fetch_letobasket_schedule()
        
        if not schedule:
            print("   📅 Расписание не найдено")
            return []
        
        # Проверяем игры сегодня
        now = get_moscow_time()
        games_to_monitor = []
        
        for game in schedule:
            if not is_today(game['date']):
                continue
                
            try:
                # Парсим время игры
                time_str = game['time'].replace('.', ':')
                game_time = datetime.strptime(f"{game['date']} {time_str}", '%d.%m.%Y %H:%M')
                game_time = game_time.replace(tzinfo=timezone(timedelta(hours=3)))  # МСК
                
                # Проверяем, начинается ли игра в ближайшие 5 минут
                time_diff = (game_time - now).total_seconds()
                
                if 0 <= time_diff <= 300:  # От 0 до 5 минут (300 секунд)
                    games_to_monitor.append(game)
                    print(f"   🏀 Игра {game['team1']} vs {game['team2']} начинается через {time_diff/60:.1f} минут")
                    
            except Exception as e:
                print(f"   ⚠️ Ошибка парсинга времени игры: {e}")
                continue
        
        if games_to_monitor:
            print(f"   ✅ Найдено {len(games_to_monitor)} игр для мониторинга")
        else:
            print(f"   ℹ️ Нет игр для мониторинга в ближайшие 5 минут")
            
        return games_to_monitor
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки игр: {e}")
        return []

async def run_game_results_monitor():
    """Запускает мониторинг результатов игр"""
    print("🏀 ЗАПУСК МОНИТОРИНГА РЕЗУЛЬТАТОВ ИГР")
    print("=" * 60)
    
    # Используем централизованное логирование времени
    now = get_moscow_time()
    print(f"🕐 Текущее время (Москва): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Проверяем игры для мониторинга
    games_to_monitor = await check_games_for_monitoring()
    
    if not games_to_monitor:
        print("📅 Нет игр для мониторинга, завершаем работу")
        return
    
    try:
        # Загружаем историю мониторинга
        monitor_history = load_game_monitor_history()
        print(f"📋 История мониторинга содержит {len(monitor_history)} записей")
        
        # Создаем экземпляр монитора
        monitor = GameResultsMonitor()
        
        # Запускаем мониторинг для каждой игры
        for game in games_to_monitor:
            print(f"\n🎮 Запускаем мониторинг для игры: {game['team1']} vs {game['team2']}")
            
            # Запускаем мониторинг (ссылка будет найдена внутри мониторинга)
            success = await monitor.start_monitoring_for_game(game, "")
            
            if success:
                print(f"   ✅ Мониторинг запущен успешно")
            else:
                print(f"   ❌ Ошибка запуска мониторинга")
        
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
